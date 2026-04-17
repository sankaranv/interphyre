"""
Benjamini-Hochberg FDR correction for the probing study (§12.5).

BH is applied within each claim group independently, not across all tests
simultaneously. This is the conservative choice: grouping by hypothesis
preserves within-group error control while avoiding excessive power loss
from cross-hypothesis pooling.

CLAIM_GROUPS maps hypothesis IDs to a human-readable description of the
test grid; the description is for audit purposes only.
"""

from __future__ import annotations

import numpy as np

try:
    from scipy.stats import false_discovery_control as _scipy_fdr

    _SCIPY_FDR_AVAILABLE = True
except ImportError:
    _SCIPY_FDR_AVAILABLE = False

try:
    from statsmodels.stats.multitest import multipletests as _sm_multipletests

    _STATSMODELS_AVAILABLE = True
except ImportError:
    _STATSMODELS_AVAILABLE = False

from ..config import FDR_Q


def apply_bh_correction(
    pvalues: np.ndarray,
    q: float = FDR_Q,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply BH FDR correction. Returns (adjusted_pvalues, is_significant).

    Priority:
    1. scipy.stats.false_discovery_control (scipy ≥ 1.11) — preferred.
    2. statsmodels multipletests(method='fdr_bh') — fallback.

    Raises ImportError if neither is available.
    """
    pvalues = np.asarray(pvalues, dtype=np.float64)

    if _SCIPY_FDR_AVAILABLE:
        adjusted = _scipy_fdr(pvalues, method="bh")
        is_significant = adjusted <= q
        return adjusted, is_significant

    if _STATSMODELS_AVAILABLE:
        reject, adjusted, _, _ = _sm_multipletests(pvalues, method="fdr_bh", alpha=q)
        return np.asarray(adjusted, dtype=np.float64), np.asarray(reject, dtype=bool)

    raise ImportError(
        "BH correction requires scipy (≥1.11) or statsmodels. "
        "Install one of them: `pip install scipy` or `pip install statsmodels`."
    )


# Claim group definitions from §12.5.
# Each value describes the test grid; used to organize tests for correction.
CLAIM_GROUPS: dict[str, str] = {
    "H1_descriptive": "1 test per (level, layer, position)",
    "H2_collapse": "1 test per (level, target, direction, layer, position)",
    "H3_core": "1 test per (level, target, direction, layer, position)",
    "H3b_llm_vs_geometric": "same grid as H3",
    "H4_precision": "1 per (level, layer, position) per H4a/b/c",
    "H5a_lolo": "1 per (held-out level, layer, position) × 2",
    "H5b_pairwise": "1 per (source, target, layer, position)",
    "H6a_behavioral": "1 per (level, target, direction, alpha)",
    "prompt_text_baseline": "1 per (level, target, direction, layer)",
}
