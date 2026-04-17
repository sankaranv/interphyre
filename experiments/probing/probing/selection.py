"""
Layer and position selection via nested cross-validation (§12.6).

The layer/position sweep is performed on inner-train/inner-val splits so that
the final eval split sees neither the probe weights nor the selected (L*, p*)
— this prevents double-dipping and ensures the eval metric is an unbiased
estimate of generalization.

Position indices:
  0 → T1: first token of the physics description
  1 → T2: last token of the physics description
  2 → T3: mean-pooled window of last T3_POOL_SIZE tokens
"""

from __future__ import annotations

import numpy as np

from .probes import fit_logistic_probe, fit_ridge_probe


def select_best_layer_position(
    scores_grid: np.ndarray,  # [n_layers, 3] inner-val scores
    layer_indices: list[int],
) -> tuple[int, int]:
    """Return (L_star, p_star) = argmax of inner-val scores.

    p_star ∈ {0, 1, 2} for T1, T2, T3 respectively.
    Ties are broken by taking the first occurrence in row-major order,
    which corresponds to the shallowest layer and earliest position — a
    conservative bias toward simpler representations.
    """
    flat_best = int(np.argmax(scores_grid))
    layer_rel, position = divmod(flat_best, 3)
    layer_abs = layer_indices[layer_rel]
    return layer_abs, position


def run_layer_position_sweep(
    X_all: np.ndarray,  # [n_train, n_layers, 3, hidden_size]
    y_train: np.ndarray,  # labels for all n_train instances
    y_val: np.ndarray,  # labels for inner_val subset
    inner_train_mask: np.ndarray,  # bool mask over n_train
    inner_val_mask: np.ndarray,
    probe_type: str,  # "logistic" or "ridge"
    layer_indices: list[int],
) -> tuple[np.ndarray, tuple[int, int]]:
    """For each (layer, position) combination, fit probe on inner-train and score on inner-val.

    Returns (scores_grid [n_layers, 3], (L_star, p_star)).

    The sweep is over the inner split only; the outer eval split is never
    touched during this function.  Probe type is passed explicitly so that
    classification and regression claims use the appropriate loss.
    """
    n_layers = len(layer_indices)
    scores_grid = np.full((n_layers, 3), fill_value=np.nan, dtype=np.float64)

    X_inner_train = X_all[inner_train_mask]  # [n_inner_train, n_layers, 3, hidden_size]
    X_inner_val = X_all[inner_val_mask]  # [n_inner_val, n_layers, 3, hidden_size]

    for layer_rel, layer_abs in enumerate(layer_indices):
        for position in range(3):
            # Extract [n, hidden_size] activations at this (layer, position).
            X_tr = X_inner_train[:, layer_rel, position, :]
            X_vl = X_inner_val[:, layer_rel, position, :]

            if probe_type == "logistic":
                probe = fit_logistic_probe(X_tr, y_train)
                score = probe.score(X_vl, y_val)
            elif probe_type == "ridge":
                probe = fit_ridge_probe(X_tr, y_train)
                score = probe.score(X_vl, y_val)
            else:
                raise ValueError(
                    f"Unknown probe_type '{probe_type}'; expected 'logistic' or 'ridge'"
                )

            scores_grid[layer_rel, position] = score

    best = select_best_layer_position(scores_grid, layer_indices)
    return scores_grid, best
