"""
Seed-disjoint split protocol for the physics-probing study (§12.2).

Design rationale:
- Splits are on seed, not on instance, to prevent data leakage across
  identical physics rollouts sharing a seed. Two instances from the same
  seed (factual + counterfactual) must stay in the same fold.
- Subset-to-successes (success_mask) is applied at conditioning time, not
  at split time, so that split proportions are computed over the seed
  population before any filtering.
"""

from __future__ import annotations

import numpy as np

try:
    from sklearn.model_selection import train_test_split

    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False

from ..config import INNER_EVAL_FRACTION, RANDOM_STATE


def within_level_split(
    seeds: list[int],
    test_size: float = INNER_EVAL_FRACTION,
    random_state: int = RANDOM_STATE,
) -> tuple[list[int], list[int]]:
    """80/20 split on seeds (not on instances).

    Returns (inner_train_seeds, inner_val_seeds). The split is on the seed
    list so that factual/counterfactual pairs sharing a seed are never split
    across train and val — this prevents any label-leakage via physics rollout
    correlation.
    """
    if not _SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn is required for within_level_split")
    train_seeds, val_seeds = train_test_split(
        seeds, test_size=test_size, random_state=random_state
    )
    return list(train_seeds), list(val_seeds)


def success_mask(factual_outcomes: np.ndarray) -> np.ndarray:
    """Boolean mask for the factual-success subset (§9.6 subset-to-successes).

    factual_outcomes: [n] bool or int. Returns [n] bool.

    Conditioning on factual success ensures the probe learns CF-outcome
    variation over scenes where the intended physics occurred — not over
    noise from failed attempts where the causal chain was broken before the
    target perturbation.
    """
    return factual_outcomes.astype(bool)


def get_conditioned_split_indices(
    instance_ids: list[str],
    metadata_df,  # pandas DataFrame with columns: instance_id, seed, factual_outcome
    split: str,  # "inner_train", "inner_val", "eval"
    train_seeds: list[int],
    eval_seeds: list[int],
    inner_train_seeds: list[int],
    inner_val_seeds: list[int],
) -> np.ndarray:
    """Return row indices (into the HDF5 file's instance ordering) for instances in:
    - the requested split, AND
    - factual_outcome == True (success_mask conditioning).

    Seed-disjoint: split is on seed, not on instance. Per §12.2.
    The HDF5 row order is defined by `instance_ids`; we return integer indices
    into that list so callers can slice the activation array directly.
    """
    split_seed_sets = {
        "inner_train": set(inner_train_seeds),
        "inner_val": set(inner_val_seeds),
        "eval": set(eval_seeds),
    }
    if split not in split_seed_sets:
        raise ValueError(
            f"Unknown split '{split}'; expected one of {list(split_seed_sets)}"
        )

    seed_set = split_seed_sets[split]

    # Index the metadata by instance_id for fast lookup.
    meta_indexed = metadata_df.set_index("instance_id")

    row_indices = []
    for row_idx, iid in enumerate(instance_ids):
        if iid not in meta_indexed.index:
            continue
        row = meta_indexed.loc[iid]
        # Seed-disjoint membership check.
        if int(row["seed"]) not in seed_set:
            continue
        # Subset-to-successes: only keep instances where factual succeeded.
        if not bool(row["factual_outcome"]):
            continue
        row_indices.append(row_idx)

    return np.array(row_indices, dtype=np.intp)


def lolo_split(
    levels: list[str],
    held_out_level: str,
    train_instance_ids_by_level: dict[str, list[str]],
    eval_instance_ids_by_level: dict[str, list[str]],
) -> tuple[list[str], list[str]]:
    """Leave-one-level-out: train on all other levels' inner-train, eval on held-out's test.

    Returns (train_instance_ids, eval_instance_ids). This split tests whether
    physics representations learned from one set of scenes transfer to an
    unseen level — a strict test of level-generalization.
    """
    train_ids = [
        iid
        for level in levels
        if level != held_out_level
        for iid in train_instance_ids_by_level[level]
    ]
    eval_ids = list(eval_instance_ids_by_level[held_out_level])
    return train_ids, eval_ids


def pairwise_transfer_splits(
    levels: list[str],
    train_instance_ids_by_level: dict[str, list[str]],
    eval_instance_ids_by_level: dict[str, list[str]],
) -> list[tuple[str, str, list[str], list[str]]]:
    """All 6 ordered pairs (A, B): train on A's inner-train, eval on B's test.

    Returns list of (source_level, target_level, train_ids, eval_ids).

    Ordered pairs include same-level entries (A==B), which serve as the
    within-level reference for the transfer comparison. Cross-level pairs
    (A≠B) quantify how much of the learned representation is level-specific.
    """
    results = []
    for source in levels:
        for target in levels:
            train_ids = list(train_instance_ids_by_level[source])
            eval_ids = list(eval_instance_ids_by_level[target])
            results.append((source, target, train_ids, eval_ids))
    return results
