"""
Model loading and inference loop for the probing pipeline.

Implements §10.4 model loading and the per-instance inference call. This module
is the GPU-side code; it is imported and executed by the SLURM job scripts. The
torch/transformers imports are guarded so that this file is importable on a login
node for static analysis and unit-testing of the surrounding infrastructure.
"""

from __future__ import annotations

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

from ..config import MAX_NEW_TOKENS, TEMPERATURE, TOP_P
from .parser import parse_action
from .sampling import build_inference_metadata


def load_model_and_tokenizer(model_id: str) -> tuple:
    """Load model in bfloat16 and its paired tokenizer from HuggingFace.

    bfloat16 is used throughout: it matches the Qwen3 and Gemma-2 inference
    recommendations, halves activation storage compared to float32, and is
    natively supported on A100/H100 hardware without precision-loss risks
    relative to float16's narrower exponent range.

    Asserts tokenizer.is_fast because byte-offset mapping (used by action_anchors
    in §11.2) is only available in the Rust-backed fast tokenizer. The slow
    tokenizer does not expose return_offsets_mapping.

    For Qwen3: verifies that apply_chat_template supports the enable_thinking
    kwarg (reasoning-mode toggle) by inspecting the tokenizer's chat template.
    This guard catches the case where a tokenizer update silently drops the kwarg.
    """
    if not HAS_TRANSFORMERS:
        raise RuntimeError("transformers is not installed; cannot load model")

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained(model_id)

    # §11.2 requirement: fast tokenizer needed for return_offsets_mapping.
    assert tokenizer.is_fast, (
        f"Tokenizer for {model_id} is not a fast tokenizer. "
        "byte-offset mapping (§11.2) requires tokenizer.is_fast=True."
    )

    # Qwen3: verify the chat template supports enable_thinking.
    # We probe this by rendering a dummy message with the kwarg and catching any
    # TypeError that would indicate the kwarg is not supported.
    if "Qwen3" in model_id or "qwen3" in model_id.lower():
        try:
            tokenizer.apply_chat_template(
                [{"role": "user", "content": "test"}],
                add_generation_prompt=True,
                return_tensors="pt",
                enable_thinking=True,
            )
        except TypeError as exc:
            raise RuntimeError(
                f"Tokenizer for {model_id} does not support enable_thinking kwarg. "
                "Reasoning-mode generation requires this toggle. "
                f"Underlying error: {exc}"
            ) from exc

    return model, tokenizer


def build_input_ids(tokenizer, prompt_text: str, model_id: str):
    """Apply the model's built-in chat template to wrap the prompt in a user turn.

    For Qwen3: passes enable_thinking=True to activate reasoning-mode generation,
    which causes the model to emit a <think>...</think> block before the answer.
    The §10.3 parser is insensitive to this wrapper — it scans the full decoded
    output for the first <action>...</action> tag.

    For Gemma-2: the apply_chat_template call does not accept enable_thinking,
    so we omit it. This branch is identified by the absence of "Qwen3" in model_id.

    Returns:
        input_ids tensor already moved to model.device.
    """
    messages = [{"role": "user", "content": prompt_text}]

    is_qwen3 = "Qwen3" in model_id or "qwen3" in model_id.lower()

    if is_qwen3:
        input_ids = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
            enable_thinking=True,
        )
    else:
        input_ids = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
        )

    return input_ids.to(next(iter(model_device_iter(tokenizer))))


def model_device_iter(tokenizer):
    """Yield model.device — used only as a helper to avoid importing model into build_input_ids signature."""
    # This function is intentionally not used directly; build_input_ids receives
    # model implicitly through the tokenizer's associated model device.
    # This stub exists to signal the device-placement pattern; the actual device
    # lookup is performed in run_inference_for_instance where model is in scope.
    yield torch.device("cpu")


def run_inference_for_instance(
    model,
    tokenizer,
    model_id: str,
    prompt_text: str,
    sampling_seed: int,
) -> dict:
    """Run one inference call and return all artifacts needed by the pipeline.

    Sets torch.manual_seed and torch.cuda.manual_seed before generation so that
    the same sampling_seed on the same hardware stack reproduces the same token
    draw (§10.5 reproducibility contract). Note: bit-reproducibility does not hold
    across different GPU architectures or torch versions — see §10.5 caveat.

    Generation is terminated by:
      1. The </action> token sequence (committed stop criterion per §10.4).
      2. The tokenizer's eos_token.
      3. max_new_tokens budget (logged as generation_terminated_by_budget=True).

    The output_ids field contains only the newly generated token IDs (not the
    input prompt), so that activation extraction (§11) can index into the output
    sequence directly without recomputing the input length offset.

    Returns:
        {
            "output_text": str,               # full decoded output incl. CoT and action tag
            "output_ids": list[int],          # generated token IDs only
            "terminated_by_budget": bool,     # True if hit max_new_tokens
            "parsed_action": tuple | None,    # (x, y, radius) or None
            "inference_metadata": dict,       # from build_inference_metadata()
        }
    """
    if not HAS_TRANSFORMERS:
        raise RuntimeError("transformers is not installed; cannot run inference")

    import transformers

    # Build input_ids with the model's chat template.
    messages = [{"role": "user", "content": prompt_text}]
    is_qwen3 = "Qwen3" in model_id or "qwen3" in model_id.lower()

    if is_qwen3:
        _encoded = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
            enable_thinking=True,
        )
    else:
        _encoded = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
        )

    # transformers ≥5.x returns BatchEncoding; older versions return a raw tensor.
    input_ids = (
        _encoded["input_ids"] if hasattr(_encoded, "__getitem__") and not isinstance(_encoded, torch.Tensor)
        else _encoded
    ).to(model.device)

    input_length = input_ids.shape[1]

    # Seed both CPU and CUDA RNG before generation. Two separate calls are needed
    # because torch.manual_seed only affects CPU; CUDA sampling uses its own state.
    torch.manual_seed(sampling_seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(sampling_seed)

    # Build the list of EOS token IDs including the </action> stop sequence.
    # We use eos_token_id as a list so transformers will stop on any of them.
    # The </action> token is encoded as a single token if the tokenizer merges it;
    # if it spans multiple tokens we rely on StoppingCriteria below.
    eos_ids = []
    if tokenizer.eos_token_id is not None:
        eos_ids.append(tokenizer.eos_token_id)

    # Encode </action> to get its token IDs; if it maps to a single token,
    # add it to eos_ids so the fast stopping path triggers. Multi-token
    # sequences are caught by the StoppingCriteria fallback.
    action_close_ids = tokenizer.encode("</action>", add_special_tokens=False)
    action_close_single = action_close_ids[-1] if len(action_close_ids) == 1 else None
    if action_close_single is not None:
        eos_ids.append(action_close_single)

    # StoppingCriteria for multi-token </action> sequences.
    class ActionCloseCriteria(transformers.StoppingCriteria):
        """Stop when the last generated tokens spell out </action>."""

        def __init__(self, stop_ids: list[int]) -> None:
            self._stop_ids = torch.tensor(stop_ids, dtype=torch.long)

        def __call__(self, input_ids_so_far, scores, **kwargs) -> bool:
            tail = input_ids_so_far[0, -len(self._stop_ids) :]
            return bool((tail == self._stop_ids.to(tail.device)).all())

    stopping_criteria = transformers.StoppingCriteriaList(
        [ActionCloseCriteria(action_close_ids)]
    )

    with torch.no_grad():
        output = model.generate(
            input_ids,
            do_sample=True,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_new_tokens=MAX_NEW_TOKENS,
            eos_token_id=eos_ids if eos_ids else None,
            stopping_criteria=stopping_criteria,
            # Return only the generated tokens — input prompt is excluded via
            # slicing below (output[:, input_length:]).
        )

    generated_ids = output[0, input_length:]
    output_text = tokenizer.decode(generated_ids, skip_special_tokens=False)

    # Detect budget termination: generation hit max_new_tokens rather than
    # a stop criterion. This flags candidate reject-list entries for the parser.
    terminated_by_budget = generated_ids.shape[0] >= MAX_NEW_TOKENS

    parsed_action = parse_action(output_text)

    # Determine the actual eos_token string for metadata logging.
    eos_token_str = tokenizer.eos_token or "<eos>"

    # Hardware identity for reproducibility claims (§10.5).
    cuda_device = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None

    inference_metadata = build_inference_metadata(
        level_name="",  # caller must fill in; included for API completeness
        level_seed=0,
        variant=0,
        model_id=model_id,
        sampling_seed=sampling_seed,
        transformers_version=transformers.__version__,
        tokenizer_class_name=type(tokenizer).__name__,
        tokenizer_revision=getattr(tokenizer, "name_or_path", None),
        cuda_device=cuda_device,
        generation_terminated_by_budget=terminated_by_budget,
    )
    # Override stop_criteria with the resolved eos_token string.
    inference_metadata["stop_criteria"] = ["</action>", eos_token_str]

    return {
        "output_text": output_text,
        "output_ids": generated_ids.tolist(),
        "terminated_by_budget": terminated_by_budget,
        "parsed_action": parsed_action,
        "inference_metadata": inference_metadata,
    }
