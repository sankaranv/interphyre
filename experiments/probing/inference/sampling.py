"""
Sampling seed generation and inference metadata logging for the probing pipeline.

Implements §10.5 deterministic per-instance sampling seed (sampling_seed_for) and
the inference_metadata record written alongside every inference call.
"""

from __future__ import annotations

import hashlib

from ..config import (
    MAX_NEW_TOKENS,
    PRIMARY_SAMPLING_NAMESPACE,
    TEMPERATURE,
    TOP_P,
)


def sampling_seed_for(
    level_name: str,
    level_seed: int,
    variant: int,
    model_id: str | None = None,
) -> int:
    """Deterministic per-instance sampling seed using blake2b (§10.5).

    blake2b is used instead of Python's built-in hash() because hash() is
    process-randomized across Python runs (PYTHONHASHSEED), making seeds
    non-reproducible across hosts. blake2b produces the same digest for the
    same key on any host and any Python version.

    For the primary model (model_id=None), the namespace is PRIMARY_SAMPLING_NAMESPACE
    ("probing"), preventing seed collisions with other pipeline components.

    For the replication model (model_id provided), the key is namespaced with
    "probing::{model_id}::" per §14.2, so replication runs draw independent
    random numbers from primary-model runs even for the same (level, seed, variant).
    """
    if model_id is None:
        key = f"{PRIMARY_SAMPLING_NAMESPACE}::{level_name}::{level_seed}::{variant}"
    else:
        key = f"probing::{model_id}::{level_name}::{level_seed}::{variant}"

    digest = hashlib.blake2b(key.encode("utf-8"), digest_size=8).digest()
    # digest_size=8 gives 64 bits; modulo 2**31 fits into a signed 32-bit int
    # which is required by torch.manual_seed on some backends.
    return int.from_bytes(digest, "big") % (2**31)


def build_inference_metadata(
    level_name: str,
    level_seed: int,
    variant: int,
    model_id: str,
    sampling_seed: int,
    transformers_version: str,
    tokenizer_class_name: str,
    tokenizer_revision: str | None,
    cuda_device: str | None,
    generation_terminated_by_budget: bool,
) -> dict:
    """Build the inference_metadata record written alongside every inference call (§10.5).

    All fields from the §10.5 metadata table are included so that any downstream
    consumer can verify reproducibility and detect library-revision drift without
    re-running the pipeline.

    The stop_criteria list is the committed set from §10.4 — it does not depend on
    the tokenizer eos_token at metadata construction time because the caller is
    responsible for passing the same criteria used during generation.
    """
    return {
        # Reproducibility fields
        "sampling_seed": sampling_seed,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "max_new_tokens": MAX_NEW_TOKENS,
        # Committed stop-criteria set per §10.4; eos_token is resolved at generation time.
        "stop_criteria": ["</action>", "<eos_token>"],
        # Model and tokenizer identity — guards against silent updates to model weights
        # or tokenizer vocabulary between runs.
        "model_id": model_id,
        "tokenizer_commit": f"{tokenizer_class_name}@{tokenizer_revision or 'unknown'}",
        "transformers_version": transformers_version,
        # Hardware identity for reproducibility claims — LLM sampling is not
        # bit-reproducible across GPU architectures even with the same seed (§10.5 caveat).
        "cuda_device": cuda_device,
        # Provenance of the instance — included so the metadata record is self-contained.
        "level_name": level_name,
        "level_seed": level_seed,
        "variant": variant,
        "generation_terminated_by_budget": generation_terminated_by_budget,
    }
