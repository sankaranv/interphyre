"""
Evaluation metrics and bootstrap confidence intervals for the probing study (§12.4).

Bootstrap CI design choices:
- Percentile bootstrap (not BCa) is used throughout — simpler, sufficient for n ≥ 100.
- Paired bootstrap for probe-vs-baseline comparisons uses identical index vectors
  for both scorers; pairing is load-bearing for statistical power because probe and
  baseline predictions are not independent (they share the same test instances).
- 'Significantly better' is declared iff the lower bound of the paired difference CI > 0.
"""

from __future__ import annotations

import numpy as np

try:
    from sklearn.metrics import (
        balanced_accuracy_score,
        mean_absolute_error,
        r2_score,
        roc_auc_score,
    )

    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False

from ..config import BOOTSTRAP_N_RESAMPLES, BOOTSTRAP_SEED


def bootstrap_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    scorer,  # callable(y_true, y_pred) -> float
    n_resamples: int = BOOTSTRAP_N_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float]:
    """95% percentile bootstrap CI per §12.4. Returns (lower, upper).

    Uses rng.integers for explicit index sampling to ensure reproducibility
    independent of global numpy random state.
    """
    rng = np.random.default_rng(seed)
    n = len(y_true)
    scores = np.empty(n_resamples, dtype=np.float64)
    for i in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        scores[i] = scorer(y_true[idx], y_pred[idx])
    lower = float(np.percentile(scores, 2.5))
    upper = float(np.percentile(scores, 97.5))
    return lower, upper


def paired_bootstrap_ci(
    y_true: np.ndarray,
    y_pred_probe: np.ndarray,
    y_pred_baseline: np.ndarray,
    scorer,
    n_resamples: int = BOOTSTRAP_N_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float]:
    """Paired bootstrap CI on (score_probe - score_baseline) per §12.4.

    Uses same index vectors for both — the pairing is load-bearing for power.
    'Significantly better' iff lower bound > 0.
    """
    rng = np.random.default_rng(seed)
    n = len(y_true)
    diffs = np.empty(n_resamples, dtype=np.float64)
    for i in range(n_resamples):
        # Shared index vector — both scorers see the same bootstrap sample.
        idx = rng.integers(0, n, size=n)
        score_probe = scorer(y_true[idx], y_pred_probe[idx])
        score_baseline = scorer(y_true[idx], y_pred_baseline[idx])
        diffs[i] = score_probe - score_baseline
    lower = float(np.percentile(diffs, 2.5))
    upper = float(np.percentile(diffs, 97.5))
    return lower, upper


def evaluate_binary_probe(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,  # [n, 2] or [n] for binary
    y_pred_labels: np.ndarray,
) -> dict:
    """Returns balanced accuracy, ROC-AUC, and their 95% bootstrap CIs.

    y_pred_proba can be [n, 2] (full probability matrix) or [n] (positive class
    probability); roc_auc_score is called with the positive-class column.
    """
    # Extract positive-class probability for AUC.
    if y_pred_proba.ndim == 2:
        pos_proba = y_pred_proba[:, 1]
    else:
        pos_proba = y_pred_proba

    bal_acc = float(balanced_accuracy_score(y_true, y_pred_labels))
    auc = float(roc_auc_score(y_true, pos_proba))

    bal_acc_ci = bootstrap_ci(y_true, y_pred_labels, balanced_accuracy_score)
    auc_ci = bootstrap_ci(y_true, pos_proba, roc_auc_score)

    return {
        "balanced_accuracy": bal_acc,
        "roc_auc": auc,
        "balanced_accuracy_ci": bal_acc_ci,
        "roc_auc_ci": auc_ci,
    }


def evaluate_regression_probe(
    y_true: np.ndarray,  # [n] or [n, k]
    y_pred: np.ndarray,
    label_std: np.ndarray | None = None,  # for MAE in physical units
    label_mean: np.ndarray | None = None,
) -> dict:
    """Returns R², raw MAE, physical-unit MAE (if label_std provided), and 95% bootstrap CIs.

    Physical-unit MAE undoes the z-score standardization applied at feature
    extraction time (§11.3), making error interpretable in the original coordinate
    system (meters or m/s). If label_std is None, mae_physical is None.
    """
    r2 = float(r2_score(y_true, y_pred))
    mae_raw = float(mean_absolute_error(y_true, y_pred))

    if label_std is not None:
        # Undo standardization: MAE in original units.
        residuals = np.abs(y_true - y_pred) * label_std
        mae_physical = float(residuals.mean())
    else:
        mae_physical = None

    r2_ci = bootstrap_ci(y_true, y_pred, r2_score)
    mae_ci = bootstrap_ci(y_true, y_pred, mean_absolute_error)

    return {
        "r2": r2,
        "mae_raw": mae_raw,
        "mae_physical": mae_physical,
        "r2_ci": r2_ci,
        "mae_ci": mae_ci,
    }
