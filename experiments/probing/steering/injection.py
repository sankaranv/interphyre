"""
Activation injection via forward hook for DIM steering (§13.2).

The hook adds α * dim_direction to the residual stream at each forward pass
through layer L*. Both Qwen3 and Gemma2 expose their residual stream as
output[0] of each decoder layer's input_layernorm sub-module, so a single
hook convention works for both architectures.
"""

from __future__ import annotations

try:
    import torch

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

import numpy as np

from ..config import MAX_NEW_TOKENS, TEMPERATURE, TOP_P
from ..inference.parser import parse_action
from ..inference.sampling import build_inference_metadata


class SteeringHook:
    """Manages the residual-stream addition hook for DIM steering.

    Adds α * dim_direction to the residual stream at every forward pass through
    layer L*. The hook is registered on model.model.layers[L_star].input_layernorm
    so that the steering vector is added to the pre-LN residual, consistent with
    the DIM intervention site described in §13.2.

    The hook must be registered before generation and removed after to avoid
    contaminating any subsequent unsteered runs.
    """

    def __init__(
        self, dim_direction: np.ndarray, alpha: float, device: str = "cpu"
    ) -> None:
        """
        Args:
            dim_direction: [d_model] numpy array (unit vector from direction.py).
            alpha: signed float controlling direction and magnitude of steering.
            device: torch device string for placing the steering tensor.
        """
        if not HAS_TORCH:
            raise RuntimeError("torch is not installed; cannot register steering hook")

        # Convert to a float32 tensor scaled by alpha once at construction time
        # to avoid repeated conversion during generation.
        steering_vec = torch.tensor(dim_direction, dtype=torch.float32, device=device)
        self._delta = (alpha * steering_vec).to(torch.bfloat16)
        self._handle: torch.utils.hooks.RemovableHook | None = None

    def hook_fn(self, module, args, output):
        """Forward hook: adds alpha * dim_direction to the residual stream.

        Both Qwen3 and Gemma2 decoder layers store the residual stream in
        output[0] when the hook is placed on input_layernorm. The hook returns
        a modified output tuple so the transformer continues with the steered
        activation.
        """
        # output may be a tensor or tuple depending on the model implementation.
        if isinstance(output, tuple):
            modified = output[0] + self._delta.to(output[0].device)
            return (modified,) + output[1:]
        else:
            return output + self._delta.to(output.device)

    def register(self, model, L_star: int) -> None:
        """Register hook at model.model.layers[L_star].input_layernorm.

        Placement on input_layernorm's forward hook means the delta is added
        to whatever tensor is fed into the LayerNorm, which is the residual
        stream at that layer depth.

        Args:
            model: a loaded HuggingFace causal LM.
            L_star: layer index at which to inject.
        """
        target_module = model.model.layers[L_star].input_layernorm
        self._handle = target_module.register_forward_hook(self.hook_fn)

    def remove(self) -> None:
        """Remove the registered hook. Safe to call multiple times."""
        if self._handle is not None:
            self._handle.remove()
            self._handle = None


def run_steered_inference(
    model,
    tokenizer,
    model_id: str,
    prompt_text: str,
    dim_direction: np.ndarray,
    alpha: float,
    L_star: int,
    sampling_seed: int,
) -> dict:
    """Run steered inference: register hook, generate, remove hook.

    Uses the same sampling hyperparameters as primary inference (TEMPERATURE,
    TOP_P, MAX_NEW_TOKENS from config). Returns the same dict structure as
    runner.run_inference_for_instance, with an additional "alpha" key recording
    the applied steering magnitude.

    The hook is always removed in a finally block to prevent state leakage
    across calls even when generation raises an exception.

    Args:
        model: loaded HuggingFace causal LM (bfloat16, device_map=auto).
        tokenizer: paired fast tokenizer.
        model_id: HuggingFace model identifier string.
        prompt_text: raw user-turn text (chat template applied inside).
        dim_direction: [d_model] unit vector from direction.py.
        alpha: signed steering magnitude.
        L_star: layer index at which to inject.
        sampling_seed: int seed for torch RNG (§10.5 reproducibility contract).

    Returns:
        Dict with keys: output_text, output_ids, terminated_by_budget,
        parsed_action, inference_metadata, alpha.
    """
    if not HAS_TORCH:
        raise RuntimeError("torch is not installed; cannot run steered inference")

    import transformers

    device = str(next(model.parameters()).device)
    hook = SteeringHook(dim_direction, alpha, device=device)

    # Determine device string for the hook tensor; bfloat16 casting happens in hook_fn.
    is_qwen3 = "Qwen3" in model_id or "qwen3" in model_id.lower()
    messages = [{"role": "user", "content": prompt_text}]

    if is_qwen3:
        input_ids = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
            enable_thinking=True,
        ).to(model.device)
    else:
        input_ids = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(model.device)

    input_length = input_ids.shape[1]

    # Seed both CPU and CUDA RNG before generation per §10.5.
    import torch as _torch

    _torch.manual_seed(sampling_seed)
    if _torch.cuda.is_available():
        _torch.cuda.manual_seed(sampling_seed)

    eos_ids = []
    if tokenizer.eos_token_id is not None:
        eos_ids.append(tokenizer.eos_token_id)

    action_close_ids = tokenizer.encode("</action>", add_special_tokens=False)
    action_close_single = action_close_ids[-1] if len(action_close_ids) == 1 else None
    if action_close_single is not None:
        eos_ids.append(action_close_single)

    class ActionCloseCriteria(transformers.StoppingCriteria):
        def __init__(self, stop_ids: list[int]) -> None:
            self._stop_ids = _torch.tensor(stop_ids, dtype=_torch.long)

        def __call__(self, input_ids_so_far, scores, **kwargs) -> bool:
            tail = input_ids_so_far[0, -len(self._stop_ids) :]
            return bool((tail == self._stop_ids.to(tail.device)).all())

    stopping_criteria = transformers.StoppingCriteriaList(
        [ActionCloseCriteria(action_close_ids)]
    )

    hook.register(model, L_star)
    try:
        with _torch.no_grad():
            output = model.generate(
                input_ids,
                do_sample=True,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                max_new_tokens=MAX_NEW_TOKENS,
                eos_token_id=eos_ids if eos_ids else None,
                stopping_criteria=stopping_criteria,
            )
    finally:
        hook.remove()

    generated_ids = output[0, input_length:]
    output_text = tokenizer.decode(generated_ids, skip_special_tokens=False)
    terminated_by_budget = generated_ids.shape[0] >= MAX_NEW_TOKENS
    parsed_action = parse_action(output_text)

    eos_token_str = tokenizer.eos_token or "<eos>"
    cuda_device = _torch.cuda.get_device_name(0) if _torch.cuda.is_available() else None

    inference_metadata = build_inference_metadata(
        level_name="",
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
    inference_metadata["stop_criteria"] = ["</action>", eos_token_str]
    inference_metadata["steering_alpha"] = alpha
    inference_metadata["steering_L_star"] = L_star

    return {
        "output_text": output_text,
        "output_ids": generated_ids.tolist(),
        "terminated_by_budget": terminated_by_budget,
        "parsed_action": parsed_action,
        "inference_metadata": inference_metadata,
        "alpha": alpha,
    }
