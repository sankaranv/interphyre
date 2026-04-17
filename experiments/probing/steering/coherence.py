"""
H6c coherence metrics for the DIM steering evaluation (§13.5).

Checks that the steered model's outputs remain interpretable at the α values
where H6a and H6b fire. Coherence is operationalized as the conjunction of
parseability (action tag present and valid) and perplexity under the unsteered
model below a calibration threshold.
"""

from __future__ import annotations

try:
    import torch

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

import numpy as np

from ..config import H6C_COHERENCE_FRACTION_THRESHOLD
from ..inference.parser import parse_action


def compute_parseable_fraction(outputs: list[str]) -> float:
    """Fraction of outputs where parse_action() succeeds.

    A parseable output contains a well-formed <action>...</action> span with
    finite (x, y, radius) values. This is the necessary condition for the
    steered model to remain on-task.

    Args:
        outputs: list of raw decoded output strings from steered runs.

    Returns:
        Float in [0, 1]; 1.0 means all outputs parsed successfully.
    """
    if not outputs:
        return 0.0
    n_parseable = sum(1 for text in outputs if parse_action(text) is not None)
    return n_parseable / len(outputs)


def compute_unsteered_perplexity(
    model,
    tokenizer,
    cot_text: str,
) -> float:
    """Per-token NLL of cot_text under the unsteered model (§13.5).

    Encodes cot_text as a standalone sequence (no chat template) and computes
    the mean per-token negative log-likelihood. This measures how surprising the
    steered model's output is relative to the unsteered distribution: very high
    perplexity indicates that steering has pushed the model to out-of-distribution
    text.

    Args:
        model: loaded HuggingFace causal LM (unsteered, eval mode).
        tokenizer: paired fast tokenizer.
        cot_text: decoded output string from a steered run.

    Returns:
        Per-token NLL (nats); lower = more coherent.
    """
    if not HAS_TORCH:
        raise RuntimeError("torch is not installed; cannot compute perplexity")

    input_ids = tokenizer.encode(cot_text, return_tensors="pt").to(model.device)
    if input_ids.shape[1] == 0:
        return float("inf")

    with torch.no_grad():
        outputs = model(input_ids, labels=input_ids)

    # model returns loss = mean NLL per token when labels are provided.
    return float(outputs.loss.item())


def calibrate_perplexity_threshold(
    model,
    tokenizer,
    training_cots: list[str],
    percentile: float = 95.0,
) -> float:
    """95th percentile of unsteered-distribution perplexity.

    Computes per-token NLL for each CoT in training_cots under the unsteered
    model and returns the requested percentile. This value becomes the
    perplexity threshold for H6c: steered outputs above this threshold are
    considered out-of-distribution and counted as incoherent.

    The calibration value is also written to calibration.json under the key
    "h6c_perplexity_threshold" for audit purposes.

    Args:
        model: loaded HuggingFace causal LM (unsteered, eval mode).
        tokenizer: paired fast tokenizer.
        training_cots: list of unsteered CoT texts from the training distribution.
        percentile: percentile at which to set the threshold (default 95.0).

    Returns:
        Perplexity threshold float.
    """
    perplexities = [
        compute_unsteered_perplexity(model, tokenizer, cot) for cot in training_cots
    ]
    threshold = float(np.percentile(perplexities, percentile))
    return threshold


def h6c_coherence_fraction(
    steered_outputs: list[str],
    perplexity_threshold: float,
    model,
    tokenizer,
) -> float:
    """Fraction of steered outputs that are both parseable and below perplexity_threshold.

    A steered output is coherent if and only if:
      1. parse_action() succeeds (on-task structure preserved), AND
      2. per-token NLL under the unsteered model < perplexity_threshold
         (reasoning text is in-distribution).

    Both conditions must hold because a model could produce a valid action tag
    with incoherent reasoning, or coherent reasoning that fails to produce a
    valid tag.

    Args:
        steered_outputs: list of decoded output strings from steered runs.
        perplexity_threshold: calibrated from calibrate_perplexity_threshold.
        model: loaded HuggingFace causal LM (unsteered, eval mode).
        tokenizer: paired fast tokenizer.

    Returns:
        Float in [0, 1]; fraction of coherent steered outputs.
    """
    if not steered_outputs:
        return 0.0
    coherent_count = 0
    for text in steered_outputs:
        if parse_action(text) is None:
            continue
        ppl = compute_unsteered_perplexity(model, tokenizer, text)
        if ppl < perplexity_threshold:
            coherent_count += 1
    return coherent_count / len(steered_outputs)


def h6c_passes(coherence_fraction: float) -> bool:
    """H6c pass criterion: coherence_fraction > H6C_COHERENCE_FRACTION_THRESHOLD.

    Per §15.3, steering must maintain interpretable outputs in > 80% of
    steered runs at the α values where H6a and H6b fire.

    Args:
        coherence_fraction: from h6c_coherence_fraction.

    Returns:
        True iff the fraction exceeds the configured threshold.
    """
    return coherence_fraction > H6C_COHERENCE_FRACTION_THRESHOLD
