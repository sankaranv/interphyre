"""
H6a behavioral-change metrics for the DIM steering evaluation (§13.3).

Measures whether the DIM steering vector produces larger behavioral changes
than random directions of matched norm. Behavioral change is quantified on two
axes: L2 distance between (x,y,r) action tuples and normalized Levenshtein
distance between CoT texts.
"""

from __future__ import annotations

import hashlib
from difflib import SequenceMatcher

import numpy as np

from ..config import H6A_MIN_PASSING_ALPHAS, H6A_RANDOM_CONTROL_N_DRAWS


def action_tuple_distance(
    action_steered: tuple[float, float, float] | None,
    action_unsteered: tuple[float, float, float] | None,
) -> float | None:
    """L2 distance between (x, y, r) action tuples.

    Returns None if either action is None (unparseable output is excluded from
    the behavioral-change distribution per §13.3, rather than being treated as
    zero change).

    Args:
        action_steered: (x, y, radius) from steered run, or None.
        action_unsteered: (x, y, radius) from unsteered run, or None.

    Returns:
        Euclidean distance in (x, y, radius) space, or None.
    """
    if action_steered is None or action_unsteered is None:
        return None
    steered_arr = np.array(action_steered, dtype=np.float64)
    unsteered_arr = np.array(action_unsteered, dtype=np.float64)
    return float(np.linalg.norm(steered_arr - unsteered_arr))


def _strip_action_tags(text: str) -> str:
    """Remove the first <action>...</action> span from a CoT string.

    The action tag is stripped before CoT edit-distance computation so that
    coordinate changes caused by steering do not dominate the text-level
    divergence signal.
    """
    import re

    return re.sub(r"<action>.*?</action>", "", text, flags=re.DOTALL).strip()


def cot_edit_distance(cot_steered: str, cot_unsteered: str) -> float:
    """Normalized Levenshtein distance between CoT texts.

    The <action>...</action> span is stripped from both texts before comparison
    so that the metric reflects reasoning-path divergence, not action-value
    divergence (which is already captured by action_tuple_distance).

    Uses SequenceMatcher's ratio(), which computes:
        2 * M / T
    where M is matching characters and T is total characters. The returned
    distance is 1 - ratio(), mapping 0.0 (identical) to 1.0 (no overlap).

    Args:
        cot_steered: full decoded output text from steered run.
        cot_unsteered: full decoded output text from unsteered run.

    Returns:
        Float in [0, 1]; higher means more divergent reasoning.
    """
    stripped_steered = _strip_action_tags(cot_steered)
    stripped_unsteered = _strip_action_tags(cot_unsteered)
    similarity = SequenceMatcher(
        None, stripped_steered, stripped_unsteered, autojunk=False
    ).ratio()
    return 1.0 - similarity


def random_controls_for(
    instance_id: str,
    alpha: float,
    d_model: int,
    n_draws: int = H6A_RANDOM_CONTROL_N_DRAWS,
) -> np.ndarray:
    """Generate random unit vectors scaled by |alpha| as null-distribution controls.

    Per §13.3: 20 random unit vectors per (instance, α), each with norm = |alpha|,
    are used to form the null distribution against which the DIM direction's
    behavioral effect is compared.

    Seed construction: 42 + int(blake2b(instance_id.encode(), digest_size=4), 16).
    This makes the draws deterministic per instance while being independent across
    instances and independent of the DIM direction.

    Args:
        instance_id: string identifier for the scene instance.
        alpha: steering magnitude; random vectors are scaled to this norm.
        d_model: residual-stream dimension.
        n_draws: number of random control vectors (default 20 per §13.3).

    Returns:
        [n_draws, d_model] float32 array; each row has L2 norm = |alpha|.
    """
    digest_hex = hashlib.blake2b(instance_id.encode(), digest_size=4).hexdigest()
    seed = 42 + int(digest_hex, 16)
    rng = np.random.default_rng(seed)

    # Sample from standard normal, then normalize to unit sphere, then scale.
    raw = rng.standard_normal((n_draws, d_model)).astype(np.float32)
    norms = np.linalg.norm(raw, axis=1, keepdims=True)
    unit_vectors = raw / (norms + 1e-12)
    return unit_vectors * abs(alpha)


def h6a_pass_at_alpha(
    steered_distances: list[float],
    random_distances: list[float],
) -> bool:
    """H6a pass criterion at one α value.

    Passes if the median behavioral change under DIM steering exceeds the 95th
    percentile of the random-direction null distribution. This tests whether
    the DIM direction induces systematically larger behavioral change than a
    direction-matched random perturbation.

    Args:
        steered_distances: DIM-steered behavioral-change scores across instances.
        random_distances: 20*n_instances random-control scores.

    Returns:
        True if median_steered > p95_random.
    """
    if not steered_distances or not random_distances:
        return False
    median_steered = float(np.median(steered_distances))
    p95_random = float(np.percentile(random_distances, 95))
    return median_steered > p95_random


def compute_h6a_result(
    per_alpha_steered_distances: dict[float, list[float]],
    per_alpha_random_distances: dict[float, list[float]],
    axis: str,
) -> dict:
    """Compute H6a pass/fail per alpha and the overall pass verdict.

    Overall pass: the DIM direction passes h6a_pass_at_alpha at ≥ H6A_MIN_PASSING_ALPHAS
    of the 10 positive-α values, per §15.3.

    Args:
        per_alpha_steered_distances: alpha -> list of per-instance distances under DIM steering.
        per_alpha_random_distances: alpha -> list of per-instance distances under random controls.
        axis: "action_tuple_l2" or "cot_edit" — recorded for provenance only.

    Returns:
        Dict mapping each alpha to {"median_steered", "p95_random", "passes"}, plus
        "overall_pass" bool and "axis" string.
    """
    result: dict = {"axis": axis}
    positive_passes = 0

    for alpha, steered in per_alpha_steered_distances.items():
        random = per_alpha_random_distances.get(alpha, [])
        median_steered = float(np.median(steered)) if steered else float("nan")
        p95_random = float(np.percentile(random, 95)) if random else float("nan")
        passes = h6a_pass_at_alpha(steered, random)
        result[alpha] = {
            "median_steered": median_steered,
            "p95_random": p95_random,
            "passes": passes,
        }
        if alpha > 0 and passes:
            positive_passes += 1

    result["overall_pass"] = positive_passes >= H6A_MIN_PASSING_ALPHAS
    return result
