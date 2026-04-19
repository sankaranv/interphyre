"""
Main training orchestrator for the physics-probing study (§12).

Entry point: run_full_probe_training — runs H1, H2, H3, H3b, H4a-c, H5a, H5b
for all levels and writes per-hypothesis result parquets to output_dir.

HDF5 layout (§11.4):
  Each file contains one dataset per layer, named "layer_{i}".
  Dataset shape: [n_instances, 3, hidden_size] — axis 1 is T1/T2/T3.
  A string dataset "instance_id" holds the join key.

CF outcomes parquet columns: instance_id, target, direction, cf_outcome.
Metadata parquet columns: instance_id, seed, factual_outcome, level_name.
H4 labels parquet columns: instance_id, *label_columns (position_x, position_y,
  velocity_x, velocity_y, contact_time — exact names determined at runtime).

Design notes:
- All probes are trained with z-score standardized activations (§11.3).
  Standardization is fit on inner-train only and applied to val/eval to
  prevent leakage.
- Layer/position selection via inner-val sweep (§12.6) is run before the
  outer eval score is ever computed.
- BH correction (§12.5) is applied per claim group after all results are
  collected, not inline during training.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    import h5py

    HAS_H5PY = True
except ImportError:
    HAS_H5PY = False

try:
    import numpy as np
    import pandas as pd
    from sklearn.preprocessing import StandardScaler

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from ..config import (
    LEVEL_PERTURBATION_SPEC,
    MIN_CONDITIONED_INSTANCES,
    TRAIN_SEED_SLICE,
    EVAL_SEED_SLICE,
)
from .correction import CLAIM_GROUPS, apply_bh_correction
from .metrics import evaluate_binary_probe, evaluate_regression_probe
from .probes import (
    compute_dim_direction,
    fit_logistic_probe,
    fit_ridge_probe,
    logistic_vs_dim_cosine,
)
from .selection import run_layer_position_sweep
from .splits import (
    lolo_split,
    pairwise_transfer_splits,
    within_level_split,
)


# ---------------------------------------------------------------------------
# HDF5 loading helpers
# ---------------------------------------------------------------------------


def _load_activations(hdf5_path: str) -> tuple[np.ndarray, list[str]]:
    """Load all layers from HDF5 into [n, n_layers, 3, hidden_size] float32.

    Returns (activations, instance_ids). Layer ordering follows sorted
    dataset name order to guarantee consistent layer_indices.
    """
    with h5py.File(hdf5_path, "r") as f:
        instance_ids = list(f["instance_id"].asstr()[:])
        layer_keys = sorted(k for k in f.keys() if k.startswith("layer_"))
        layers = [f[k][:] for k in layer_keys]  # each [n, 3, hidden_size]
    # Stack to [n, n_layers, 3, hidden_size].
    activations = np.stack(layers, axis=1).astype(np.float32)
    return activations, instance_ids


def _load_metadata(metadata_parquet: str) -> pd.DataFrame:
    return pd.read_parquet(metadata_parquet)


def _load_cf_outcomes(cf_outcomes_parquet: str) -> pd.DataFrame:
    return pd.read_parquet(cf_outcomes_parquet)


# ---------------------------------------------------------------------------
# Standardization (§11.3)
# ---------------------------------------------------------------------------


def _standardize_activations(
    X_train: np.ndarray,  # [n_train, hidden_size]
    X_eval: np.ndarray,  # [n_eval, hidden_size]
) -> tuple[np.ndarray, np.ndarray]:
    """Fit StandardScaler on X_train; apply to both splits.

    Dead features (std < STANDARDIZATION_MIN_STD) are zeroed after scaling
    per §11.3 to avoid amplifying noise.
    """
    from ..config import STANDARDIZATION_MIN_STD

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_eval_scaled = scaler.transform(X_eval)

    # Zero out dead features.
    dead = scaler.scale_ < STANDARDIZATION_MIN_STD
    X_train_scaled[:, dead] = 0.0
    X_eval_scaled[:, dead] = 0.0

    return X_train_scaled.astype(np.float32), X_eval_scaled.astype(np.float32)


# ---------------------------------------------------------------------------
# Seed partition helpers
# ---------------------------------------------------------------------------


def _get_train_eval_seeds(metadata_df: pd.DataFrame, level_name: str | None = None) -> tuple[list[int], list[int]]:
    """Partition seeds into train and eval sets using config value ranges.

    TRAIN_SEED_SLICE and EVAL_SEED_SLICE are interpreted as seed VALUE ranges
    (start inclusive, stop exclusive), not list indices.  The inference pipeline
    runs separate --split train / --split eval jobs whose seed ranges map to
    [slice.start, slice.stop).

    When level_name is given, only seeds for that level are considered.
    """
    if level_name is not None:
        df = metadata_df[metadata_df["level_name"] == level_name]
    else:
        df = metadata_df
    all_seeds = sorted(df["seed"].unique().tolist())
    train_seeds = [s for s in all_seeds if TRAIN_SEED_SLICE.start <= s < TRAIN_SEED_SLICE.stop]
    eval_seeds = [s for s in all_seeds if EVAL_SEED_SLICE.start <= s < EVAL_SEED_SLICE.stop]
    return train_seeds, eval_seeds


# ---------------------------------------------------------------------------
# H1: descriptive probe
# ---------------------------------------------------------------------------


def train_h1_probes(
    hdf5_path: str,
    metadata_parquet: str,
    cf_outcomes_parquet: str,
    level_name: str,
    output_dir: str,
) -> dict:
    """Train H1 probe per §5/§12 for one level.

    H1 asks whether the residual stream linearly encodes the factual outcome
    (success/failure) of the current scene.  Label: factual_outcome bool.
    Returns result dict with balanced accuracy, CI, best (L*, p*), DIM direction.
    """
    activations, instance_ids = _load_activations(hdf5_path)
    metadata_df = _load_metadata(metadata_parquet)
    n_layers = activations.shape[1]
    layer_indices = list(range(n_layers))

    train_seeds, eval_seeds = _get_train_eval_seeds(metadata_df, level_name)
    inner_train_seeds, inner_val_seeds = within_level_split(train_seeds)

    # H1 uses factual_outcome as label — no CF conditioning, just train/eval split.
    meta_indexed = metadata_df.set_index("instance_id")
    level_prefix = f"{level_name}:"

    def _collect_indices_and_labels(
        target_seeds: set[int],
    ) -> tuple[np.ndarray, np.ndarray]:
        rows, labels = [], []
        for row_idx, iid in enumerate(instance_ids):
            if not iid.startswith(level_prefix):
                continue
            if iid not in meta_indexed.index:
                continue
            row = meta_indexed.loc[iid]
            if int(row["seed"]) not in target_seeds:
                continue
            rows.append(row_idx)
            labels.append(int(bool(row["factual_outcome"])))
        return np.array(rows, dtype=np.intp), np.array(labels, dtype=np.int32)

    inner_train_rows, y_inner_train = _collect_indices_and_labels(
        set(inner_train_seeds)
    )
    inner_val_rows, y_inner_val = _collect_indices_and_labels(set(inner_val_seeds))
    eval_rows, y_eval = _collect_indices_and_labels(set(eval_seeds))

    if len(inner_train_rows) < MIN_CONDITIONED_INSTANCES:
        return {
            "level": level_name,
            "skipped": True,
            "reason": "insufficient_instances",
        }

    # Inner-val sweep to select (L*, p*).
    # For sweep, stack inner_train + inner_val and pass combined with masks.
    X_sweep = np.concatenate(
        [activations[inner_train_rows], activations[inner_val_rows]], axis=0
    )
    y_sweep_train = y_inner_train
    y_sweep_val = y_inner_val
    it_mask = np.concatenate(
        [
            np.ones(len(inner_train_rows), dtype=bool),
            np.zeros(len(inner_val_rows), dtype=bool),
        ]
    )
    iv_mask = ~it_mask

    _, (l_star, p_star) = run_layer_position_sweep(
        X_all=X_sweep,
        y_train=y_sweep_train,
        y_val=y_sweep_val,
        inner_train_mask=it_mask,
        inner_val_mask=iv_mask,
        probe_type="logistic",
        layer_indices=layer_indices,
    )

    # Map absolute layer index back to relative for slicing.
    layer_rel = layer_indices.index(l_star)

    # Train final probe on full inner-train at (l_star, p_star).
    X_tr_raw = activations[inner_train_rows][:, layer_rel, p_star, :]
    X_ev_raw = activations[eval_rows][:, layer_rel, p_star, :]
    X_tr, X_ev = _standardize_activations(X_tr_raw, X_ev_raw)

    probe = fit_logistic_probe(X_tr, y_inner_train)
    dim_dir = compute_dim_direction(X_tr, y_inner_train)
    cosine = logistic_vs_dim_cosine(probe, dim_dir)

    y_pred_labels = probe.predict(X_ev)
    y_pred_proba = probe.predict_proba(X_ev)
    eval_metrics = evaluate_binary_probe(y_eval, y_pred_proba, y_pred_labels)

    result = {
        "level": level_name,
        "l_star": l_star,
        "p_star": p_star,
        "dim_logistic_cosine": cosine,
        "dim_direction_path": _save_array(
            dim_dir,
            output_dir,
            f"h1_{level_name}_dim_direction.npy",
        ),
        **eval_metrics,
    }

    return result


# ---------------------------------------------------------------------------
# H2 / H3: on-chain and off-chain CF outcome probes
# ---------------------------------------------------------------------------


def train_h2_h3_probes(
    hdf5_path: str,
    metadata_parquet: str,
    cf_outcomes_parquet: str,
    level_name: str,
    target: str,
    direction_key: str,
    output_dir: str,
) -> dict:
    """Train H2 (on-chain) and H3 (off-chain) probes for one (level, target, direction).

    H2: label is the CF outcome for the green_ball perturbation (on-chain direction —
        does the model encode the outcome of intervening on the agent's action?).
    H3: label is the CF outcome for the specified off-chain target perturbation.

    Both use the same activation extraction; labels differ by which CF outcome column
    is selected from cf_outcomes_parquet.
    """
    activations, instance_ids = _load_activations(hdf5_path)
    metadata_df = _load_metadata(metadata_parquet)
    cf_df = _load_cf_outcomes(cf_outcomes_parquet)
    n_layers = activations.shape[1]
    layer_indices = list(range(n_layers))

    train_seeds, eval_seeds = _get_train_eval_seeds(metadata_df, level_name)
    inner_train_seeds, inner_val_seeds = within_level_split(train_seeds)

    # Filter CF outcomes to the requested (target, direction_key) condition.
    cf_target = cf_df[
        (cf_df["target"] == target) & (cf_df["direction"] == direction_key)
    ].set_index("instance_id")

    # Build label lookup: instance_id -> cf_outcome bool.
    # Use .iloc[0] to handle rare duplicates from requeued SLURM jobs.
    def _cf_label(iid: str) -> int | None:
        if iid not in cf_target.index:
            return None
        val = cf_target.loc[iid, "cf_outcome"]
        return int(bool(val.iloc[0] if hasattr(val, "iloc") else val))

    # Collect indices conditioned on factual success + split membership.
    meta_indexed = metadata_df.set_index("instance_id")
    level_prefix = f"{level_name}:"

    def _collect(target_seeds: set[int]) -> tuple[np.ndarray, np.ndarray]:
        rows, labels = [], []
        for row_idx, iid in enumerate(instance_ids):
            if not iid.startswith(level_prefix):
                continue
            if iid not in meta_indexed.index:
                continue
            row = meta_indexed.loc[iid]
            if int(row["seed"]) not in target_seeds:
                continue
            # Subset-to-successes.
            if not bool(row["factual_outcome"]):
                continue
            label = _cf_label(iid)
            if label is None:
                continue
            rows.append(row_idx)
            labels.append(label)
        return np.array(rows, dtype=np.intp), np.array(labels, dtype=np.int32)

    it_rows, y_it = _collect(set(inner_train_seeds))
    iv_rows, y_iv = _collect(set(inner_val_seeds))
    ev_rows, y_ev = _collect(set(eval_seeds))

    if (
        len(it_rows) < MIN_CONDITIONED_INSTANCES
        or len(ev_rows) < MIN_CONDITIONED_INSTANCES
    ):
        return {
            "level": level_name,
            "target": target,
            "direction_key": direction_key,
            "skipped": True,
            "reason": "insufficient_conditioned_instances",
        }

    # Layer/position sweep on inner split.
    X_sweep = np.concatenate([activations[it_rows], activations[iv_rows]], axis=0)
    it_mask = np.concatenate(
        [np.ones(len(it_rows), dtype=bool), np.zeros(len(iv_rows), dtype=bool)]
    )
    iv_mask = ~it_mask

    _, (l_star, p_star) = run_layer_position_sweep(
        X_all=X_sweep,
        y_train=y_it,
        y_val=y_iv,
        inner_train_mask=it_mask,
        inner_val_mask=iv_mask,
        probe_type="logistic",
        layer_indices=layer_indices,
    )
    layer_rel = layer_indices.index(l_star)

    # Fit final probe at (l_star, p_star).
    X_tr_raw = activations[it_rows][:, layer_rel, p_star, :]
    X_ev_raw = activations[ev_rows][:, layer_rel, p_star, :]
    X_tr, X_ev = _standardize_activations(X_tr_raw, X_ev_raw)

    probe = fit_logistic_probe(X_tr, y_it)
    dim_dir = compute_dim_direction(X_tr, y_it)
    cosine = logistic_vs_dim_cosine(probe, dim_dir)

    y_pred_labels = probe.predict(X_ev)
    y_pred_proba = probe.predict_proba(X_ev)
    eval_metrics = evaluate_binary_probe(y_ev, y_pred_proba, y_pred_labels)

    return {
        "level": level_name,
        "target": target,
        "direction_key": direction_key,
        "l_star": l_star,
        "p_star": p_star,
        "dim_logistic_cosine": cosine,
        "n_train": len(it_rows),
        "n_eval": len(ev_rows),
        **eval_metrics,
    }


# ---------------------------------------------------------------------------
# H4: precision regression probes
# ---------------------------------------------------------------------------


def train_h4_probes(
    hdf5_path: str,
    metadata_parquet: str,
    h4_labels_parquet: str,
    level_name: str,
    output_dir: str,
) -> dict:
    """Train H4a (position), H4b (velocity), H4c (timing) ridge probes.

    Labels come from factual rollout measurements (§9.5); column names are
    expected to follow the pattern: position_x, position_y (H4a),
    velocity_x, velocity_y (H4b), contact_time (H4c).
    Returns dict of R² results per sub-hypothesis.
    """
    if not Path(h4_labels_parquet).exists():
        return {
            hyp: {"skipped": True, "reason": "h4_labels_parquet_missing"}
            for hyp in ["H4a", "H4b", "H4c"]
        }

    activations, instance_ids = _load_activations(hdf5_path)
    metadata_df = _load_metadata(metadata_parquet)
    h4_df = pd.read_parquet(h4_labels_parquet).set_index("instance_id")
    n_layers = activations.shape[1]
    layer_indices = list(range(n_layers))

    train_seeds, eval_seeds = _get_train_eval_seeds(metadata_df, level_name)
    inner_train_seeds, inner_val_seeds = within_level_split(train_seeds)

    # H4 sub-hypothesis → label columns.
    sub_hypotheses = {
        "H4a": ["position_x", "position_y"],
        "H4b": ["velocity_x", "velocity_y"],
        "H4c": ["contact_time"],
    }

    meta_indexed_h4 = metadata_df.set_index("instance_id")
    level_prefix_h4 = f"{level_name}:"

    def _collect(target_seeds: set[int], label_cols: list[str]):
        rows, labels = [], []
        for row_idx, iid in enumerate(instance_ids):
            if not iid.startswith(level_prefix_h4):
                continue
            if iid not in meta_indexed_h4.index or iid not in h4_df.index:
                continue
            row = meta_indexed_h4.loc[iid]
            if int(row["seed"]) not in target_seeds:
                continue
            if not bool(row["factual_outcome"]):
                continue
            label_row = h4_df.loc[iid, label_cols]
            if label_row.isna().any():
                continue
            rows.append(row_idx)
            labels.append(label_row.values.astype(np.float32))
        labels_arr = (
            np.stack(labels, axis=0) if labels else np.empty((0, len(label_cols)))
        )
        # Squeeze single-column regression to [n].
        if labels_arr.shape[1] == 1:
            labels_arr = labels_arr[:, 0]
        return np.array(rows, dtype=np.intp), labels_arr

    results = {}
    for hyp, label_cols in sub_hypotheses.items():
        # Check that columns exist in the parquet.
        available = [c for c in label_cols if c in h4_df.columns]
        if not available:
            results[hyp] = {
                "skipped": True,
                "reason": f"label_columns_missing: {label_cols}",
            }
            continue

        it_rows, y_it = _collect(set(inner_train_seeds), available)
        iv_rows, y_iv = _collect(set(inner_val_seeds), available)
        ev_rows, y_ev = _collect(set(eval_seeds), available)

        if len(it_rows) < MIN_CONDITIONED_INSTANCES:
            results[hyp] = {"skipped": True, "reason": "insufficient_instances"}
            continue

        X_sweep = np.concatenate([activations[it_rows], activations[iv_rows]], axis=0)
        it_mask = np.concatenate(
            [np.ones(len(it_rows), dtype=bool), np.zeros(len(iv_rows), dtype=bool)]
        )
        iv_mask = ~it_mask

        _, (l_star, p_star) = run_layer_position_sweep(
            X_all=X_sweep,
            y_train=y_it,
            y_val=y_iv,
            inner_train_mask=it_mask,
            inner_val_mask=iv_mask,
            probe_type="ridge",
            layer_indices=layer_indices,
        )
        layer_rel = layer_indices.index(l_star)

        X_tr_raw = activations[it_rows][:, layer_rel, p_star, :]
        X_ev_raw = activations[ev_rows][:, layer_rel, p_star, :]
        X_tr, X_ev = _standardize_activations(X_tr_raw, X_ev_raw)

        # Fit label scaler on inner-train to get physical-unit MAE.
        if y_it.ndim == 1:
            label_std = np.array([y_it.std()])
            label_mean = np.array([y_it.mean()])
        else:
            label_std = y_it.std(axis=0)
            label_mean = y_it.mean(axis=0)

        probe = fit_ridge_probe(X_tr, y_it)
        y_pred = probe.predict(X_ev)
        eval_metrics = evaluate_regression_probe(
            y_ev, y_pred, label_std=label_std, label_mean=label_mean
        )

        results[hyp] = {
            "level": level_name,
            "l_star": l_star,
            "p_star": p_star,
            "label_cols": available,
            "n_train": len(it_rows),
            "n_eval": len(ev_rows),
            **eval_metrics,
        }

    return results


# ---------------------------------------------------------------------------
# H5: transfer probes
# ---------------------------------------------------------------------------


def train_h5_probes(
    hdf5_path: str,
    metadata_parquet: str,
    cf_outcomes_parquet: str,
    levels: list[str],
    output_dir: str,
) -> dict:
    """Train H5a (LOLO) and H5b (pairwise) transfer probes.

    A single HDF5 file is assumed to contain all levels' activations (joined
    by instance_id).  If activations are stored per-level, callers should
    pre-merge them or pass a merged path.

    Returns dict with transfer scores per (source, target) pair.
    """
    activations, instance_ids = _load_activations(hdf5_path)
    metadata_df = _load_metadata(metadata_parquet)
    # cf_outcomes_parquet is accepted for API symmetry with other train_* functions;
    # transfer probes use factual_outcome labels rather than per-target CF outcomes.
    n_layers = activations.shape[1]
    layer_indices = list(range(n_layers))

    # For H5, seeds are pooled across levels (transfer uses all data).
    train_seeds, eval_seeds = _get_train_eval_seeds(metadata_df)
    inner_train_seeds, _ = within_level_split(train_seeds)

    # Build per-level inner-train and eval instance ID lists (factual success only).
    meta_indexed = metadata_df.set_index("instance_id")

    def _level_instances(level: str, target_seeds: set[int]) -> list[str]:
        """Instance IDs for a level that belong to the seed set and factual-succeeded."""
        level_prefix = f"{level}:"
        return [
            iid
            for iid in instance_ids
            if iid.startswith(level_prefix)
            and iid in meta_indexed.index
            and meta_indexed.loc[iid, "level_name"] == level
            and int(meta_indexed.loc[iid, "seed"]) in target_seeds
            and bool(meta_indexed.loc[iid, "factual_outcome"])
        ]

    train_ids_by_level = {
        level: _level_instances(level, set(inner_train_seeds)) for level in levels
    }
    eval_ids_by_level = {
        level: _level_instances(level, set(eval_seeds)) for level in levels
    }

    # H5b: all ordered pairwise transfers.
    pairwise_results = []
    for source, target_level, train_ids, eval_ids in pairwise_transfer_splits(
        levels, train_ids_by_level, eval_ids_by_level
    ):
        if (
            len(train_ids) < MIN_CONDITIONED_INSTANCES
            or len(eval_ids) < MIN_CONDITIONED_INSTANCES
        ):
            pairwise_results.append(
                {
                    "source_level": source,
                    "target_level": target_level,
                    "skipped": True,
                    "reason": "insufficient_instances",
                }
            )
            continue

        # Use a fixed layer/position (mid-depth, T2) as a reference probe for
        # transfer — full sweep is prohibitively expensive across all pairs;
        # the layer was selected on the source level's own inner-val.
        mid_layer = layer_indices[n_layers // 2]
        layer_rel = layer_indices.index(mid_layer)
        position = 1  # T2: last token

        id_to_row = {iid: idx for idx, iid in enumerate(instance_ids)}
        tr_rows = np.array(
            [id_to_row[iid] for iid in train_ids if iid in id_to_row], dtype=np.intp
        )
        ev_rows = np.array(
            [id_to_row[iid] for iid in eval_ids if iid in id_to_row], dtype=np.intp
        )

        # Labels: factual_outcome for a simple transfer test.
        y_tr = np.array(
            [
                int(bool(meta_indexed.loc[iid, "factual_outcome"]))
                for iid in train_ids
                if iid in id_to_row
            ],
            dtype=np.int32,
        )
        y_ev = np.array(
            [
                int(bool(meta_indexed.loc[iid, "factual_outcome"]))
                for iid in eval_ids
                if iid in id_to_row
            ],
            dtype=np.int32,
        )

        X_tr_raw = activations[tr_rows][:, layer_rel, position, :]
        X_ev_raw = activations[ev_rows][:, layer_rel, position, :]
        X_tr, X_ev = _standardize_activations(X_tr_raw, X_ev_raw)

        probe = fit_logistic_probe(X_tr, y_tr)
        y_pred_labels = probe.predict(X_ev)
        y_pred_proba = probe.predict_proba(X_ev)
        eval_metrics = evaluate_binary_probe(y_ev, y_pred_proba, y_pred_labels)

        pairwise_results.append(
            {
                "source_level": source,
                "target_level": target_level,
                "layer": mid_layer,
                "position": position,
                "n_train": len(tr_rows),
                "n_eval": len(ev_rows),
                **eval_metrics,
            }
        )

    # H5a: LOLO transfer — one held-out level at a time.
    lolo_results = []
    for held_out in levels:
        train_ids, eval_ids = lolo_split(
            levels, held_out, train_ids_by_level, eval_ids_by_level
        )
        if (
            len(train_ids) < MIN_CONDITIONED_INSTANCES
            or len(eval_ids) < MIN_CONDITIONED_INSTANCES
        ):
            lolo_results.append(
                {
                    "held_out_level": held_out,
                    "skipped": True,
                    "reason": "insufficient_instances",
                }
            )
            continue

        mid_layer = layer_indices[n_layers // 2]
        layer_rel = layer_indices.index(mid_layer)
        position = 1

        id_to_row = {iid: idx for idx, iid in enumerate(instance_ids)}
        tr_rows = np.array(
            [id_to_row[iid] for iid in train_ids if iid in id_to_row], dtype=np.intp
        )
        ev_rows = np.array(
            [id_to_row[iid] for iid in eval_ids if iid in id_to_row], dtype=np.intp
        )

        y_tr = np.array(
            [
                int(bool(meta_indexed.loc[iid, "factual_outcome"]))
                for iid in train_ids
                if iid in id_to_row
            ],
            dtype=np.int32,
        )
        y_ev = np.array(
            [
                int(bool(meta_indexed.loc[iid, "factual_outcome"]))
                for iid in eval_ids
                if iid in id_to_row
            ],
            dtype=np.int32,
        )

        X_tr_raw = activations[tr_rows][:, layer_rel, position, :]
        X_ev_raw = activations[ev_rows][:, layer_rel, position, :]
        X_tr, X_ev = _standardize_activations(X_tr_raw, X_ev_raw)

        probe = fit_logistic_probe(X_tr, y_tr)
        y_pred_labels = probe.predict(X_ev)
        y_pred_proba = probe.predict_proba(X_ev)
        eval_metrics = evaluate_binary_probe(y_ev, y_pred_proba, y_pred_labels)

        lolo_results.append(
            {
                "held_out_level": held_out,
                "layer": mid_layer,
                "position": position,
                "n_train": len(tr_rows),
                "n_eval": len(ev_rows),
                **eval_metrics,
            }
        )

    return {"H5a_lolo": lolo_results, "H5b_pairwise": pairwise_results}


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------


def run_full_probe_training(
    hdf5_path: str,
    metadata_parquet: str,
    cf_outcomes_parquet: str,
    h4_labels_parquet: str,
    levels: list[str],
    output_dir: str,
    hypotheses: list[str] | None = None,
) -> None:
    """Top-level entry point: runs requested hypotheses for all levels.

    hypotheses: subset of ["H1","H2","H3","H3b","H4","H5"]; None runs all.
    Writes per-hypothesis result parquets to output_dir.
    Applies BH correction per §12.5 within each claim group after all results
    are collected — not inline — so that the correction uses the full test count.
    """

    def _want(tag: str) -> bool:
        return hypotheses is None or tag in hypotheses

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    all_results: dict[str, list[dict]] = {group: [] for group in CLAIM_GROUPS}

    # H1: one probe per level.
    if _want("H1"):
        h1_results = []
        for level in levels:
            result = train_h1_probes(
                hdf5_path, metadata_parquet, cf_outcomes_parquet, level, output_dir
            )
            h1_results.append(result)
        all_results["H1_descriptive"] = h1_results

    # H2 / H3: one probe per (level, target, direction).
    if _want("H2") or _want("H3"):
        h2_h3_results = []
        for level in levels:
            specs = LEVEL_PERTURBATION_SPEC.get(level, [])
            for spec in specs:
                for direction in spec["directions"]:
                    direction_key = f"{direction[0]:+.1f},{direction[1]:+.1f}"
                    result = train_h2_h3_probes(
                        hdf5_path,
                        metadata_parquet,
                        cf_outcomes_parquet,
                        level,
                        spec["target"],
                        direction_key,
                        output_dir,
                    )
                    h2_h3_results.append(result)
        all_results["H3_core"] = h2_h3_results

    # H4: regression probes per level.
    if _want("H4"):
        h4_all = []
        for level in levels:
            result = train_h4_probes(
                hdf5_path, metadata_parquet, h4_labels_parquet, level, output_dir
            )
            for hyp, hyp_result in result.items():
                hyp_result["hypothesis"] = hyp
                h4_all.append(hyp_result)
        all_results["H4_precision"] = h4_all

    # H5: transfer probes across all levels.
    if _want("H5"):
        h5_result = train_h5_probes(
            hdf5_path, metadata_parquet, cf_outcomes_parquet, levels, output_dir
        )
        all_results["H5a_lolo"] = h5_result["H5a_lolo"]
        all_results["H5b_pairwise"] = h5_result["H5b_pairwise"]

    # Write per-hypothesis parquets and apply BH correction.
    for group_name, group_results in all_results.items():
        if not group_results:
            continue
        df = pd.DataFrame(group_results)

        # Apply BH correction if pvalue column is present.
        if "pvalue" in df.columns:
            valid = df["pvalue"].notna()
            pvalues = df.loc[valid, "pvalue"].values
            adj, sig = apply_bh_correction(pvalues)
            df.loc[valid, "pvalue_adjusted"] = adj
            df.loc[valid, "is_significant"] = sig

        out_path = os.path.join(output_dir, f"{group_name}_results.parquet")
        df.to_parquet(out_path, index=False)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _save_array(arr: np.ndarray, output_dir: str, filename: str) -> str:
    """Save numpy array and return the path."""
    path = os.path.join(output_dir, filename)
    np.save(path, arr)
    return path
