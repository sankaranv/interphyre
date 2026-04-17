"""
DIM steering direction computation for H6 (§13.1–13.2).

Implements difference-in-means (DIM) per §6 and §13.1: the steering direction
is mean(X[y==1]) - mean(X[y==0]), unit-normalized. This is the Bayes-optimal
linear separator under Gaussian equal-covariance and requires no optimization.
LinearSVC is explicitly NOT used — it optimizes a margin objective that deforms
the direction away from the class-separation axis (§6 footnote).
"""

from __future__ import annotations

import json
from pathlib import Path

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from ..config import (
    ALPHA_GRID_LOWER_FACTOR,
    ALPHA_GRID_N_POINTS,
    ALPHA_GRID_UPPER_FACTOR,
)


def compute_steering_direction(
    activations_Lstar_pstar: "np.ndarray",
    labels: "np.ndarray",
) -> "np.ndarray":
    """Compute unit-normalized DIM direction on activations at (L*, p*).

    DIM = mean(X[labels==1]) - mean(X[labels==0]), unit-normalized (§13.1).
    Labels: 1 = fragile (CF outcome flips), 0 = robust. The returned vector
    points from the robust centroid toward the fragile centroid.

    Args:
        activations_Lstar_pstar: [n_train, d_model] float32, z-scored per §11.3.
        labels: [n_train] int {0, 1}; 1 = fragile, 0 = robust.

    Returns:
        [d_model] float32 unit vector oriented toward fragile class.
    """
    if not HAS_NUMPY:
        raise RuntimeError("numpy is not installed; cannot compute DIM direction")
    mean_fragile = activations_Lstar_pstar[labels == 1].mean(axis=0)
    mean_robust = activations_Lstar_pstar[labels == 0].mean(axis=0)
    raw_direction = (mean_fragile - mean_robust).astype(np.float32)
    unit_direction = raw_direction / (np.linalg.norm(raw_direction) + 1e-12)
    return unit_direction


def compute_norm_Lstar(activations_Lstar_pstar: np.ndarray) -> float:
    """Mean L2 norm of post-z-score activations at (L*, p*).

    Used by §13.2 to set the α grid in units of the typical activation
    magnitude at the intervention site, ensuring the grid spans a
    physically interpretable range of perturbation strengths.

    Args:
        activations_Lstar_pstar: [n_train, d_model] float32, z-scored.

    Returns:
        Mean L2 norm across the n_train instances.
    """
    norms = np.linalg.norm(activations_Lstar_pstar, axis=1)
    return float(np.mean(norms))


def build_alpha_grid(norm_Lstar: float) -> np.ndarray:
    """Build the 21-value α grid for the steering sweep (§13.2).

    Grid design:
      - 10 negative-α values: log-spaced from -ALPHA_GRID_LOWER_FACTOR*norm
        to -ALPHA_GRID_UPPER_FACTOR*norm (i.e. from small-magnitude to
        large-magnitude negative, so the array is sorted ascending).
      - 0 at center.
      - 10 positive-α values: log-spaced from ALPHA_GRID_LOWER_FACTOR*norm
        to ALPHA_GRID_UPPER_FACTOR*norm.

    Log-spacing is used so that both subtle and strong interventions are
    sampled, matching §13.2's intent of spanning roughly one decade on each
    side of zero.

    Args:
        norm_Lstar: calibration scalar from compute_norm_Lstar.

    Returns:
        [21] float64 array in ascending order.
    """
    low = ALPHA_GRID_LOWER_FACTOR * norm_Lstar
    high = ALPHA_GRID_UPPER_FACTOR * norm_Lstar

    positive_alphas = np.logspace(np.log10(low), np.log10(high), ALPHA_GRID_N_POINTS)
    negative_alphas = -positive_alphas[::-1]  # descending magnitude → ascending value

    return np.concatenate([negative_alphas, [0.0], positive_alphas])


def save_steering_direction(
    dim_direction: np.ndarray,
    norm_Lstar: float,
    alpha_grid: np.ndarray,
    level_name: str,
    target: str,
    direction_key: str,
    L_star: int,
    p_star: int,
    calibration_json_path: str,
) -> None:
    """Append steering direction info to calibration.json.

    Stores the direction vector, calibration norm, alpha grid, and layer/position
    under the nested key ``{level_name}/{target}/{direction_key}/steering``.
    Creates the JSON file if absent; reads and merges if present.

    Args:
        dim_direction: [d_model] unit vector from compute_steering_direction.
        norm_Lstar: calibration scalar from compute_norm_Lstar.
        alpha_grid: [21] float array from build_alpha_grid.
        level_name: e.g. "down_to_earth".
        target: perturbation target name, e.g. "purple_ground".
        direction_key: e.g. "pos_x" (encodes direction vector identity).
        L_star: optimal layer index.
        p_star: optimal position index.
        calibration_json_path: absolute or project-relative path to calibration.json.
    """
    cal_path = Path(calibration_json_path)
    cal_path.parent.mkdir(parents=True, exist_ok=True)

    data: dict = {}
    if cal_path.exists():
        with cal_path.open("r") as f:
            data = json.load(f)

    # Build nested path level_name -> target -> direction_key -> steering
    data.setdefault(level_name, {})
    data[level_name].setdefault(target, {})
    data[level_name][target].setdefault(direction_key, {})
    data[level_name][target][direction_key]["steering"] = {
        "dim_direction": dim_direction.tolist(),
        "norm_Lstar": norm_Lstar,
        "alpha_grid": alpha_grid.tolist(),
        "L_star": L_star,
        "p_star": p_star,
    }

    with cal_path.open("w") as f:
        json.dump(data, f, indent=2)
