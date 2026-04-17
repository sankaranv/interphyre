"""
Headline results table T1 for the probing study (§15.1).

T1 is a per-(hypothesis, level, operationalization) pass/fail table that
records the primary metric, 95% CI, baseline comparison, and paired-bootstrap
difference CI used for all claims in §15.4.
"""

from __future__ import annotations

from pathlib import Path

try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from ..config import (
    H1_H3_BALANCED_ACC_THRESHOLD,
    H4_R2_THRESHOLD,
)

# Column contract for T1 — all downstream consumers depend on these names.
T1_COLUMNS = [
    "hypothesis",
    "level",
    "operationalization",
    "balanced_accuracy_or_r2",
    "ci_lower",
    "ci_upper",
    "baseline_score",
    "baseline_ci_upper",
    "paired_diff_ci_lower",
    "pass_verdict",
]


def _pass_h1_h3(ci_lower: float, threshold: float) -> bool:
    """H1/H3 pass: lower CI > threshold per §15.3."""
    return ci_lower > threshold


def _pass_h4(ci_lower: float) -> bool:
    """H4 pass: lower CI on R² > H4_R2_THRESHOLD per §15.3."""
    return ci_lower > H4_R2_THRESHOLD


def build_headline_table(
    h1_results: dict,
    h3_results: dict,
    h3b_results: dict,
    h4_results: dict,
    thresholds: dict | None = None,
) -> "pd.DataFrame":
    """Build T1: per-hypothesis pass/fail table.

    Aggregates results from H1, H3, H3b, and H4a/b/c into a single DataFrame
    with a uniform column schema. Pass verdicts are computed from §15.3 rules:
    H1/H3/H3b require lower-CI > threshold; H4 requires lower-CI on R² > 0.2.

    Args:
        h1_results: {level_name: {"acc", "ci": (lower, upper), "baseline_acc",
            "baseline_ci": (lower, upper), "paired_diff_ci": (lower, upper)}}.
        h3_results: {level_name: {(target, direction): same schema as h1}}.
        h3b_results: same schema as h3_results but for the H3b operationalization.
        h4_results: {sub_hyp: {level_name: {"r2", "ci": (lower, upper),
            "baseline_r2", "baseline_ci": (lower, upper),
            "paired_diff_ci": (lower, upper)}}}.
        thresholds: optional override dict with keys "h1_h3" and "h4"; falls
            back to config values if None.

    Returns:
        DataFrame with columns defined by T1_COLUMNS.
    """
    h1_h3_thresh = (
        thresholds.get("h1_h3", H1_H3_BALANCED_ACC_THRESHOLD)
        if thresholds
        else H1_H3_BALANCED_ACC_THRESHOLD
    )

    if not HAS_PANDAS:
        raise RuntimeError("pandas is not installed; cannot build headline table")

    rows: list[dict] = []

    # H1 rows: one per level.
    for level, data in h1_results.items():
        ci = data.get("ci", (float("nan"), float("nan")))
        baseline_ci = data.get("baseline_ci", (float("nan"), float("nan")))
        paired_ci = data.get("paired_diff_ci", (float("nan"), float("nan")))
        acc = data.get("acc", float("nan"))
        rows.append(
            {
                "hypothesis": "H1",
                "level": level,
                "operationalization": "factual_success",
                "balanced_accuracy_or_r2": acc,
                "ci_lower": ci[0],
                "ci_upper": ci[1],
                "baseline_score": data.get("baseline_acc", float("nan")),
                "baseline_ci_upper": baseline_ci[1],
                "paired_diff_ci_lower": paired_ci[0],
                "pass_verdict": _pass_h1_h3(ci[0], h1_h3_thresh),
            }
        )

    # H3 rows: one per (level, target, direction).
    for level, conditions in h3_results.items():
        for (target, direction), data in conditions.items():
            ci = data.get("ci", (float("nan"), float("nan")))
            baseline_ci = data.get("baseline_ci", (float("nan"), float("nan")))
            paired_ci = data.get("paired_diff_ci", (float("nan"), float("nan")))
            acc = data.get("acc", float("nan"))
            rows.append(
                {
                    "hypothesis": "H3",
                    "level": level,
                    "operationalization": f"{target}/{direction}",
                    "balanced_accuracy_or_r2": acc,
                    "ci_lower": ci[0],
                    "ci_upper": ci[1],
                    "baseline_score": data.get("baseline_acc", float("nan")),
                    "baseline_ci_upper": baseline_ci[1],
                    "paired_diff_ci_lower": paired_ci[0],
                    "pass_verdict": _pass_h1_h3(ci[0], h1_h3_thresh),
                }
            )

    # H3b rows: same schema as H3.
    for level, conditions in h3b_results.items():
        for (target, direction), data in conditions.items():
            ci = data.get("ci", (float("nan"), float("nan")))
            baseline_ci = data.get("baseline_ci", (float("nan"), float("nan")))
            paired_ci = data.get("paired_diff_ci", (float("nan"), float("nan")))
            acc = data.get("acc", float("nan"))
            rows.append(
                {
                    "hypothesis": "H3b",
                    "level": level,
                    "operationalization": f"{target}/{direction}",
                    "balanced_accuracy_or_r2": acc,
                    "ci_lower": ci[0],
                    "ci_upper": ci[1],
                    "baseline_score": data.get("baseline_acc", float("nan")),
                    "baseline_ci_upper": baseline_ci[1],
                    "paired_diff_ci_lower": paired_ci[0],
                    "pass_verdict": _pass_h1_h3(ci[0], h1_h3_thresh),
                }
            )

    # H4a/b/c rows: one per (sub_hypothesis, level).
    for sub_hyp, level_data in h4_results.items():
        for level, data in level_data.items():
            ci = data.get("ci", (float("nan"), float("nan")))
            baseline_ci = data.get("baseline_ci", (float("nan"), float("nan")))
            paired_ci = data.get("paired_diff_ci", (float("nan"), float("nan")))
            r2 = data.get("r2", float("nan"))
            rows.append(
                {
                    "hypothesis": sub_hyp,
                    "level": level,
                    "operationalization": "continuous_regression",
                    "balanced_accuracy_or_r2": r2,
                    "ci_lower": ci[0],
                    "ci_upper": ci[1],
                    "baseline_score": data.get("baseline_r2", float("nan")),
                    "baseline_ci_upper": baseline_ci[1],
                    "paired_diff_ci_lower": paired_ci[0],
                    "pass_verdict": _pass_h4(ci[0]),
                }
            )

    return pd.DataFrame(rows, columns=T1_COLUMNS)


def write_headline_table(df: "pd.DataFrame", output_path: str) -> None:
    """Write T1 as both CSV and formatted markdown.

    Creates output_path.csv and output_path.md. The markdown table is
    formatted with aligned columns and boolean pass/fail rendered as
    "PASS" / "FAIL" for readability.

    Args:
        df: DataFrame from build_headline_table.
        output_path: file stem (no extension); extensions .csv and .md are added.
    """
    if not HAS_PANDAS:
        raise RuntimeError("pandas is not installed; cannot write headline table")

    stem = Path(output_path).with_suffix("")
    stem.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(str(stem) + ".csv", index=False)

    # Render pass_verdict as readable strings and format floats to 3 d.p.
    display_df = df.copy()
    display_df["pass_verdict"] = display_df["pass_verdict"].map(
        {True: "PASS", False: "FAIL"}
    )
    float_cols = [
        "balanced_accuracy_or_r2",
        "ci_lower",
        "ci_upper",
        "baseline_score",
        "baseline_ci_upper",
        "paired_diff_ci_lower",
    ]
    for col in float_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(
                lambda v: f"{v:.3f}" if pd.notna(v) else "NaN"
            )

    with open(str(stem) + ".md", "w") as f:
        f.write(display_df.to_markdown(index=False))
        f.write("\n")
