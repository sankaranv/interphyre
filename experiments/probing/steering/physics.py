"""
H6b physics-consistency harness for the DIM steering evaluation (§13.4).

Tests whether adding the DIM steering vector to the residual stream shifts
the model's counterfactual-flip rate in the direction predicted by the probe's
fragile/robust classification: positive-α should increase CF-flip rate (more
fragile) and negative-α should decrease it (more robust), producing a
monotone relationship captured by Spearman ρ.
"""

from __future__ import annotations

import numpy as np

try:
    from scipy import stats

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

from ..config import H6B_ASYMMETRIC_EXCLUSION_MAX_DIFF


def compute_delta_cf_flip_rate(
    steered_cf_flip_rate: float,
    unsteered_cf_flip_rate: float,
) -> float:
    """ΔCF-flip-rate(α) = steered − unsteered.

    Positive values indicate the steered model is more sensitive to
    counterfactual perturbations; negative values indicate reduced sensitivity.

    Args:
        steered_cf_flip_rate: fraction of instances where CF outcome flips
            under the steered model at a given α.
        unsteered_cf_flip_rate: same fraction under the unsteered model.

    Returns:
        Signed difference in [−1, 1].
    """
    return steered_cf_flip_rate - unsteered_cf_flip_rate


def compute_h6b_spearman_rho(
    alpha_grid: np.ndarray,
    mean_delta_per_alpha: list[float],
) -> tuple[float, float]:
    """Spearman rank correlation between α and per-α mean ΔCF-flip-rate.

    A positive ρ with CI lower bound > H6B_SPEARMAN_RHO_THRESHOLD (§15.3)
    confirms that the DIM direction causally shifts physics-relevant behaviour
    in the direction predicted by the fragile/robust distinction.

    Args:
        alpha_grid: [n_alphas] array of alpha values (should span negative to positive).
        mean_delta_per_alpha: per-α mean ΔCF-flip-rate; same length as alpha_grid.

    Returns:
        (rho, p_value) from scipy.stats.spearmanr.
    """
    if not HAS_SCIPY:
        raise RuntimeError("scipy is not installed; cannot compute Spearman ρ")
    rho, p_value = stats.spearmanr(alpha_grid, mean_delta_per_alpha)
    return float(rho), float(p_value)


def h6b_bootstrap_ci(
    alpha_grid: np.ndarray,
    per_alpha_per_instance_deltas: dict[float, list[float]],
    n_resamples: int = 1000,
    seed: int = 42,
) -> tuple[float, float]:
    """Bootstrap CI on the Spearman ρ by resampling instances at each alpha.

    At each bootstrap iteration, instance-level ΔCF-flip-rate values are
    resampled with replacement at every alpha, the per-α mean is recomputed,
    and Spearman ρ is recalculated against alpha_grid. The 2.5th and 97.5th
    percentiles of the bootstrap distribution give the 95% CI.

    Resampling is done at the instance level (not the alpha level) to respect
    the correlation structure across alphas within a single scene.

    Args:
        alpha_grid: [n_alphas] alpha values in the same order as
            per_alpha_per_instance_deltas keys.
        per_alpha_per_instance_deltas: alpha -> list of per-instance ΔCF-flip-rates.
        n_resamples: number of bootstrap replicates.
        seed: random seed for reproducibility.

    Returns:
        (lower, upper) 95% CI on ρ.
    """
    rng = np.random.default_rng(seed)
    alphas_ordered = [float(a) for a in alpha_grid]
    # Stack deltas as a [n_alphas, n_instances] array (pad shorter lists with NaN).
    n_instances = max(len(v) for v in per_alpha_per_instance_deltas.values())
    delta_matrix = np.full((len(alphas_ordered), n_instances), np.nan)
    for i, alpha in enumerate(alphas_ordered):
        vals = per_alpha_per_instance_deltas.get(alpha, [])
        delta_matrix[i, : len(vals)] = vals

    bootstrap_rhos: list[float] = []
    if not HAS_SCIPY:
        raise RuntimeError(
            "scipy is not installed; cannot compute bootstrap CI on Spearman ρ"
        )
    for _ in range(n_resamples):
        # Resample instance indices with replacement.
        indices = rng.integers(0, n_instances, size=n_instances)
        resampled = delta_matrix[:, indices]
        # Compute per-alpha mean ignoring NaNs (excluded instances).
        per_alpha_means = np.nanmean(resampled, axis=1)
        rho, _ = stats.spearmanr(alphas_ordered, per_alpha_means)
        bootstrap_rhos.append(float(rho))

    lower = float(np.percentile(bootstrap_rhos, 2.5))
    upper = float(np.percentile(bootstrap_rhos, 97.5))
    return lower, upper


def check_asymmetric_exclusion(
    positive_alpha_exclusion_rates: dict[float, float],
    negative_alpha_exclusion_rates: dict[float, float],
) -> dict[float, bool]:
    """Flag alphas where positive/negative exclusion rates differ by > 20pp.

    Per §13.4: if positive-α interventions produce many more excluded instances
    (unparseable or out-of-bounds outputs) than negative-α interventions of the
    same magnitude, the behavioral asymmetry may confound the ΔCF-flip-rate
    signal. This function identifies such magnitude levels for manual review.

    Args:
        positive_alpha_exclusion_rates: |alpha| -> fraction of instances excluded
            under positive-α steering.
        negative_alpha_exclusion_rates: |alpha| -> fraction of instances excluded
            under negative-α steering (keyed by absolute magnitude).

    Returns:
        Dict mapping each |alpha| magnitude to True if the exclusion-rate
        difference exceeds H6B_ASYMMETRIC_EXCLUSION_MAX_DIFF.
    """
    all_magnitudes = set(positive_alpha_exclusion_rates) | set(
        negative_alpha_exclusion_rates
    )
    flags: dict[float, bool] = {}
    for mag in all_magnitudes:
        pos_rate = positive_alpha_exclusion_rates.get(mag, 0.0)
        neg_rate = negative_alpha_exclusion_rates.get(mag, 0.0)
        diff = abs(pos_rate - neg_rate)
        flags[mag] = diff > H6B_ASYMMETRIC_EXCLUSION_MAX_DIFF
    return flags
