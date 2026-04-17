"""
Summary template instantiation for the probing study (§15.5).

Each executed hypothesis produces one summary file at results/probing/<task_id>_summary.md.
The SUMMARY_TEMPLATE enforces a fixed structure that auditors can scan in a fixed
reading order: advisor sentence → hypothesis → setup → results → consistency → deviations.
"""

from __future__ import annotations

from pathlib import Path

SUMMARY_TEMPLATE = """# Summary: {hypothesis_id} — {descriptor}

## Advisor sentence
{advisor_sentence}

## Hypothesis (from §5)
{hypothesis_text}

## Setup
- **Dataset:** {dataset_description}
- **Model:** {model_description}
- **Conditioning:** §9.6 subset-to-successes, seed-disjoint split per §12.2.
- **Probe class and hyperparameters:** {probe_description}
- **Baseline:** {baseline_description}
- **Metric and CI:** {metric_description}
- **Seeds:** random_state=42 per §12.2.

## Results
- **Primary metric (point estimate + 95% CI):** {primary_metric}
- **Baseline metric (point estimate + 95% CI):** {baseline_metric}
- **Paired-bootstrap difference (primary − baseline, 95% CI):** {paired_diff}
- **BH-adjusted p-value:** {bh_pvalue}
- **Layer / position where reported:** {layer_position}

## Consistency with hypothesis
- **Pass per §15.3 threshold:** {pass_verdict}
- **Interpretation:** {interpretation}

## Design decisions that deviate from the plan
{deviations}

## Artifact path
{artifact_path}
"""

# Advisor sentences per §15.2 — one sentence per figure that states the
# scientific claim the figure supports, in a form an advisor can read at a glance.
ADVISOR_SENTENCES: dict[str, str] = {
    "F1": (
        "On the primary model, a linear probe on residual-stream activations at CoT tokens "
        "recovers the model's own action's factual success with balanced accuracy above the "
        "§15.3 threshold at some depth in every in-scope level — i.e., the activation-extraction "
        "and probe-training pipeline is functional before any downstream hypothesis is interpreted."
    ),
    "F2": (
        "On the primary model, a linear probe on CoT-token activations predicts the outcome "
        "of perturbing the designated off-chain target with balanced-accuracy-lower-CI above 0.55 "
        "and above the stronger geometric baseline's upper-CI in every in-scope level — "
        "establishing that the representation encodes off-chain scene sensitivity beyond action "
        "quality and beyond MLP-extractable scene geometry."
    ),
    "F3": (
        "The LLM probe's test-set R² on final green-ball position (H4a), velocity magnitude "
        "at first green–target contact (H4b), and steps-to-first-contact (H4c) exceeds the "
        "scene+action baseline's upper-CI with a lower-CI above 0.2 in at least one "
        "sub-hypothesis — establishing that the representation encodes continuous physical state "
        "not trivially recoverable from the explicit inputs."
    ),
    "F4": (
        "The H3 probe direction trained on one level of the same-structure family transfers to "
        "held-out levels — across all 6 ordered pairs (H5b) and in the LOLO setting (H5a) — "
        "with balanced accuracy above chance and above the same-level geometric-baseline upper-CI, "
        "establishing that the representation is shared across same-structure levels rather than "
        "level-specific."
    ),
    "F5": (
        "Adding the DIM steering vector to the residual stream at layer L* produces "
        "(a) larger behavioral change than random directions of matched norm at ≥ 6 of 10 "
        "positive-α values, (b) a physics-consistent shift in off-chain CF-flip rate "
        "(Spearman ρ between α and ΔCF-flip-rate > 0, CI-lower > 0.3), and "
        "(c) preserved coherence (parseable-and-below-perplexity-threshold fraction > 0.8) "
        "at the α values where (a) and (b) fire — establishing that the probe direction plays "
        "a causal role in the model's reasoning rather than being a decodable byproduct."
    ),
    "T1": (
        "The numerical per-(level, operationalization) pass/fail outcomes of H1, H3, H3b, and "
        "H4a/b/c on the primary model match the §15.3 thresholds in the directions predicted by "
        "§5, after §12.5's BH correction — and the paper's headline claim about Demo B (§15.4) "
        "is supported by these numbers and not by any single cherry-picked cell."
    ),
}


def write_hypothesis_summary(
    hypothesis_id: str,
    descriptor: str,
    advisor_sentence: str,
    hypothesis_text: str,
    results: dict,
    output_path: str,
) -> None:
    """Instantiate the SUMMARY_TEMPLATE and write to output_path.

    The results dict must contain keys matching the template's {field} names
    (excluding hypothesis_id, descriptor, advisor_sentence, hypothesis_text,
    which are passed as explicit arguments). Missing keys are filled with
    "NOT RECORDED" to prevent a KeyError from hiding partial results.

    Required keys in results:
        dataset_description, model_description, probe_description,
        baseline_description, metric_description, primary_metric,
        baseline_metric, paired_diff, bh_pvalue, layer_position,
        pass_verdict, interpretation, deviations, artifact_path.

    Args:
        hypothesis_id: short identifier, e.g. "H3" or "H4a".
        descriptor: human-readable label, e.g. "purple_ground/pos_x".
        advisor_sentence: one-sentence scientific claim for §15.2.
        hypothesis_text: the plan's §5 hypothesis statement verbatim.
        results: dict of template field values (see above).
        output_path: absolute path where the summary .md file is written.
    """
    # Fill in all template fields, defaulting missing ones so partial results
    # still produce a readable file rather than raising KeyError.
    template_fields = {
        "hypothesis_id": hypothesis_id,
        "descriptor": descriptor,
        "advisor_sentence": advisor_sentence,
        "hypothesis_text": hypothesis_text,
        "dataset_description": results.get("dataset_description", "NOT RECORDED"),
        "model_description": results.get("model_description", "NOT RECORDED"),
        "probe_description": results.get("probe_description", "NOT RECORDED"),
        "baseline_description": results.get("baseline_description", "NOT RECORDED"),
        "metric_description": results.get("metric_description", "NOT RECORDED"),
        "primary_metric": results.get("primary_metric", "NOT RECORDED"),
        "baseline_metric": results.get("baseline_metric", "NOT RECORDED"),
        "paired_diff": results.get("paired_diff", "NOT RECORDED"),
        "bh_pvalue": results.get("bh_pvalue", "NOT RECORDED"),
        "layer_position": results.get("layer_position", "NOT RECORDED"),
        "pass_verdict": results.get("pass_verdict", "NOT RECORDED"),
        "interpretation": results.get("interpretation", "NOT RECORDED"),
        "deviations": results.get("deviations", "None."),
        "artifact_path": results.get("artifact_path", "NOT RECORDED"),
    }

    content = SUMMARY_TEMPLATE.format(**template_fields)

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content)
