"""
Residual-stream hook registration per §11.1.

Hooks capture the pre-layernorm residual stream at each transformer block by
attaching to input_layernorm.forward. This is the value that has accumulated
all residual-stream updates through layer L-1 but has not yet been modified by
block L's attention or MLP. The captured tensor is detached and moved to CPU
immediately to avoid retaining GPU memory across the full generation loop.

For the embed_tokens hook (L=-1), the output of embed_tokens is captured instead
— this is the pre-block-0 embedding before any transformer processing.
"""

from __future__ import annotations


def register_residual_hooks(
    model,
    layer_indices: list[int],
    include_embed: bool = False,
) -> tuple[list, dict[int, list]]:
    """Register forward hooks on input_layernorm for each layer in layer_indices.

    Each hook appends a detached CPU copy of the pre-layernorm residual-stream
    tensor to buffers[L]. One tensor is appended per forward call (both prompt
    prefill and each autoregressive decoding step), so the buffer grows as
    generation proceeds.

    For embed_tokens (L=-1, enabled by include_embed=True), the hook is placed
    on model.model.embed_tokens and captures the output embedding tensor.

    Args:
        model: AutoModelForCausalLM (Qwen3 or Gemma 2).
        layer_indices: list of block indices to hook, e.g. list(range(36)).
        include_embed: if True, also hook embed_tokens output at key -1.

    Returns:
        (hook_handles, buffers)
        hook_handles: list of handle objects; call .remove() to deregister.
        buffers: dict[int, list] mapping layer index -> list of captured tensors.
    """
    buffers: dict[int, list] = {L: [] for L in layer_indices}
    if include_embed:
        buffers[-1] = []

    hook_handles: list = []

    # §11.1: hook input_layernorm to capture the pre-layernorm residual stream.
    # The first positional argument to input_layernorm.forward is the residual
    # stream tensor before layernorm scaling is applied.
    for layer_idx in layer_indices:
        layer_module = model.model.layers[layer_idx].input_layernorm

        def make_pre_ln_hook(buf_key: int):
            def hook(module, args, output):
                # args[0] is the residual-stream tensor before layernorm.
                # Detach and move to CPU so GPU memory is released immediately.
                buf = buffers[buf_key]
                buf.append(args[0].detach().cpu())

            return hook

        handle = layer_module.register_forward_hook(make_pre_ln_hook(layer_idx))
        hook_handles.append(handle)

    # §11.1: optional embed_tokens output hook at key -1.
    if include_embed:

        def embed_hook(module, args, output):
            buffers[-1].append(output.detach().cpu())

        handle = model.model.embed_tokens.register_forward_hook(embed_hook)
        hook_handles.append(handle)

    return hook_handles, buffers


def remove_hooks(hook_handles: list) -> None:
    """Deregister all hooks cleanly."""
    for handle in hook_handles:
        handle.remove()


def clear_buffers(buffers: dict[int, list]) -> None:
    """Clear all captured tensors from buffers (call between instances)."""
    for key in buffers:
        buffers[key].clear()
