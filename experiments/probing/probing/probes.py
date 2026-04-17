"""
Probe classes for the physics-probing study (§12.1).

Three probe types are implemented:
  - DIM (difference-in-means): closed-form direction, no tuning needed.
  - Logistic: L2-regularized linear classifier, C grid-searched via 5-fold CV.
  - Ridge: L2-regularized regression, α grid-searched via 5-fold CV.

The DIM/logistic cosine check (§12.1) audits whether classes are approximately
Gaussian — if the assumption holds the logistic weight and DIM direction should
be near-parallel.
"""

from __future__ import annotations

import numpy as np

try:
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.model_selection import GridSearchCV
    from sklearn.multioutput import MultiOutputRegressor

    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False

from ..config import LOGISTIC_C_GRID, RANDOM_STATE, RIDGE_ALPHA_GRID


def compute_dim_direction(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Compute unit-normalized DIM direction: mean(X[y==1]) - mean(X[y==0]).

    X: [n, d_model] float32. y: [n] int {0, 1}.
    Returns [d_model] float32 unit vector.
    """
    pos_mean = X[y == 1].mean(axis=0)
    neg_mean = X[y == 0].mean(axis=0)
    direction = pos_mean - neg_mean
    norm = np.linalg.norm(direction)
    if norm < 1e-12:
        return direction.astype(np.float32)
    return (direction / norm).astype(np.float32)


def fit_logistic_probe(
    X_train: np.ndarray,
    y_train: np.ndarray,
    c_grid: list[float] | None = None,
) -> "GridSearchCV":
    """Fit L2-regularized logistic probe per §12.1.

    Uses solver='liblinear', class_weight='balanced', cv=5,
    scoring='balanced_accuracy'. class_weight='balanced' compensates for
    unequal success/failure rates after subset-to-successes conditioning.
    """
    if not _SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn is required for logistic probes")
    if c_grid is None:
        c_grid = LOGISTIC_C_GRID

    base = LogisticRegression(
        penalty="l2",
        solver="liblinear",
        class_weight="balanced",
        random_state=RANDOM_STATE,
        max_iter=1000,
    )
    search = GridSearchCV(
        base,
        param_grid={"C": c_grid},
        cv=5,
        scoring="balanced_accuracy",
        refit=True,
        n_jobs=-1,
    )
    search.fit(X_train, y_train)
    return search


def fit_ridge_probe(
    X_train: np.ndarray,
    y_train: np.ndarray,  # can be [n] or [n, k] for multi-output
    alpha_grid: list[float] | None = None,
) -> "GridSearchCV":
    """Fit Ridge regression probe per §12.1.

    Alpha grid cross-validated on 5-fold CV. Multi-output labels ([n, k])
    are handled via MultiOutputRegressor wrapping — each output is fit
    independently with the same alpha, which is the correct interpretation
    for per-coordinate regression (H4a position, H4b velocity).
    """
    if not _SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn is required for ridge probes")
    if alpha_grid is None:
        alpha_grid = RIDGE_ALPHA_GRID

    multi_output = y_train.ndim == 2 and y_train.shape[1] > 1

    if multi_output:
        base = MultiOutputRegressor(Ridge(random_state=RANDOM_STATE))
        param_grid = {"estimator__alpha": alpha_grid}
    else:
        base = Ridge(random_state=RANDOM_STATE)
        param_grid = {"alpha": alpha_grid}

    search = GridSearchCV(
        base,
        param_grid=param_grid,
        cv=5,
        scoring="r2",
        refit=True,
        n_jobs=-1,
    )
    search.fit(X_train, y_train)
    return search


def logistic_vs_dim_cosine(
    logistic_probe: GridSearchCV,
    dim_direction: np.ndarray,
) -> float:
    """Cosine similarity between logistic probe weight vector (L2-normalized) and DIM direction.

    Audit of the Gaussian-class assumption per §12.1: near-parallel directions
    (|cosine| ≈ 1) indicate the probe has learned the same subspace as DIM,
    consistent with linearly-separable Gaussian classes.
    """
    weight = logistic_probe.best_estimator_.coef_.ravel()
    weight_norm = np.linalg.norm(weight)
    if weight_norm < 1e-12:
        return 0.0
    weight_unit = weight / weight_norm
    return float(np.dot(weight_unit, dim_direction))
