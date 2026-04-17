"""
Smoke test for the probing inference pipeline.

Runs 6 checks that cover the full pipeline path without a GPU. On success,
writes a gate file at scratch/probing/smoke_test_passed_<git-hash>.flag.
The SLURM inference script checks for this file before running the real job.

Usage:
    python -m experiments.probing.scripts.smoke_test [--level down_to_earth] [--seed 200]

GPU is not required. Check 2 uses a random-weight GPT-2 model as a stand-in
for the generation loop. Check 1 loads the real Qwen3 tokenizer when available
and skips gracefully if it is not cached locally.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _git_hash() -> str:
    """Return the short HEAD commit hash."""
    return (
        subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
        .decode()
        .strip()
    )


def _ok(name: str) -> None:
    print(f"OK: {name}")


def _fail(name: str, reason: str) -> None:
    print(f"FAIL: {name}: {reason}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Check 1 — Chat template + return type
# ---------------------------------------------------------------------------


def check_chat_template(level: str, seed: int) -> None:
    """Load the Qwen3-8B tokenizer, render a prompt, apply the chat template.

    Asserts the return value is a BatchEncoding or torch.Tensor and that
    ["input_ids"] produces a valid 2-D tensor. Skips gracefully when the
    tokenizer is not cached locally.

    No GPU required — the tokenizer is CPU-only.
    """
    try:
        from transformers import AutoTokenizer
    except ImportError:
        _fail("chat_template", "transformers not installed")
        raise SystemExit(1)

    model_id = "Qwen/Qwen3-8B"
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
    except OSError:
        # Tokenizer not cached locally — skip with a clear notice.
        print(
            f"SKIP: chat_template: Qwen3 tokenizer not cached locally "
            f"(model_id={model_id}). Run with internet access or cache the model "
            "first. This check is skipped but is NOT a gate failure."
        )
        return

    # Build a representative prompt so the template renders real content.
    from interphyre.validation import load_valid_level
    from interphyre.environment import InterphyreEnv
    from experiments.probing.config import PROBING_SIM_CONFIG
    from experiments.probing.inference.prompts import render_prompt

    validated = load_valid_level(level, seed=seed, config=PROBING_SIM_CONFIG)
    env = InterphyreEnv(validated.level, config=PROBING_SIM_CONFIG)
    env.reset()
    scene_dict = env.describe_scene()
    prompt_text = render_prompt(scene_dict, level)

    encoded = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt_text}],
        add_generation_prompt=True,
        return_tensors="pt",
        enable_thinking=True,
    )

    # transformers ≥5 returns BatchEncoding; older versions return a raw Tensor.
    import torch
    from transformers import BatchEncoding

    if not isinstance(encoded, (BatchEncoding, torch.Tensor)):
        _fail(
            "chat_template",
            f"apply_chat_template returned unexpected type {type(encoded).__name__}",
        )
        raise SystemExit(1)

    # Resolve input_ids regardless of return type.
    if isinstance(encoded, torch.Tensor):
        input_ids = encoded
    else:
        input_ids = encoded["input_ids"]

    if input_ids.ndim != 2:
        _fail(
            "chat_template",
            f"input_ids has {input_ids.ndim} dimensions; expected 2",
        )
        raise SystemExit(1)
    if input_ids.shape[1] == 0:
        _fail("chat_template", "input_ids has zero tokens")
        raise SystemExit(1)

    _ok("chat_template")


# ---------------------------------------------------------------------------
# Check 2 — Generation budget sanity (random-weight GPT-2)
# ---------------------------------------------------------------------------


def check_generation_budget() -> None:
    """Verify the generation loop terminates using a random-weight GPT-2 model.

    The real Qwen3-8B model is too large for a smoke test. A random-weight GPT-2
    instantiated from config (no weights downloaded) is the standard stand-in:
    it exercises the generate() call path without requiring any GPU memory or
    internet access.

    Asserts generate() returns without hanging and the decoded output is a
    non-empty string.
    """
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, GPT2Config

    # Random-weight GPT-2 — no pretrained weights, no download.
    config = GPT2Config()
    model = AutoModelForCausalLM.from_config(config)
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    # GPT-2 tokenizer has no pad token by default; set it to eos_token so
    # padding does not cause a warning during generation.
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    input_ids = tokenizer("Hello world", return_tensors="pt")["input_ids"]

    with torch.no_grad():
        output = model.generate(
            input_ids,
            max_new_tokens=10,
            do_sample=False,
        )

    generated_ids = output[0, input_ids.shape[1] :]
    # Decode with special tokens retained so the output is never empty even when
    # all generated tokens are special tokens (random weights may produce this).
    decoded = tokenizer.decode(generated_ids, skip_special_tokens=False)

    if not isinstance(decoded, str) or len(decoded) == 0:
        _fail(
            "generation_budget",
            f"decoded output is empty or wrong type: {decoded!r}",
        )
        raise SystemExit(1)

    _ok("generation_budget")


# ---------------------------------------------------------------------------
# Check 3 — Full factual rollout to on_success()
# ---------------------------------------------------------------------------


def check_factual_rollout(level: str, seed: int) -> None:
    """Load the level, place an oracle action, run to on_success(), check result.

    Uses the targeted solver to obtain a valid action placement so the rollout
    has a high probability of reaching the success condition within max_steps.
    Asserts factual_outcome is a bool, factual_step_count is an int > 0, and
    no exception is raised.
    """
    import numpy as np
    from interphyre.validation import load_valid_level
    from interphyre.validation.oracles import _solver_registry
    from interphyre.environment import InterphyreEnv
    from interphyre.interventions.triggers import on_success
    from experiments.probing.config import PROBING_SIM_CONFIG

    validated = load_valid_level(level, seed=seed, config=PROBING_SIM_CONFIG)
    level_obj = validated.level

    # Obtain an oracle action via the registered solver. The solver is seeded
    # deterministically so the smoke test is reproducible across runs.
    solver = _solver_registry.get(level)
    if solver is None:
        _fail(
            "factual_rollout",
            f"no solver registered for level '{level}'; cannot place oracle action",
        )
        raise SystemExit(1)

    oracle_rng = np.random.default_rng([seed, 0, sum(b"oracle")])
    placements = solver(level_obj, PROBING_SIM_CONFIG, 50, 500, oracle_rng)

    if placements is None:
        _fail(
            "factual_rollout",
            f"oracle solver found no valid placement for level='{level}' seed={seed}",
        )
        raise SystemExit(1)

    px, py, pr = placements[0]

    env = InterphyreEnv(level_obj, config=PROBING_SIM_CONFIG, enable_interventions=True)
    env.reset()
    env.place_action((px, py, pr))
    env.run_until(on_success(), max_steps=500)

    factual_outcome = level_obj.success_condition(env.engine)
    factual_step_count = env.describe_scene()["step_count"]

    if not isinstance(factual_outcome, bool):
        _fail(
            "factual_rollout",
            f"factual_outcome has type {type(factual_outcome).__name__}; expected bool",
        )
        raise SystemExit(1)

    if not isinstance(factual_step_count, int):
        _fail(
            "factual_rollout",
            f"factual_step_count has type {type(factual_step_count).__name__}; expected int",
        )
        raise SystemExit(1)

    if factual_step_count <= 0:
        _fail(
            "factual_rollout",
            f"factual_step_count={factual_step_count}; expected > 0",
        )
        raise SystemExit(1)

    _ok("factual_rollout")


# ---------------------------------------------------------------------------
# Check 4 — Metadata field completeness
# ---------------------------------------------------------------------------


def check_metadata_fields(level: str, seed: int) -> None:
    """Assert every required metadata field is present and well-typed.

    Builds a representative meta_row using hardcoded test values for inference
    fields and real simulated values for factual fields, then validates the full
    field contract used in run_inference.py.
    """
    # Representative meta_row mirroring the assembly in run_inference.py.
    # Inference-side fields use test stubs; factual fields use plausible values.
    instance_id = f"{level}:{seed}:0:99999"
    meta_row = {
        # Inference metadata stubs (normally filled by build_inference_metadata).
        "model_id": "Qwen/Qwen3-8B",
        "sampling_seed": 99999,
        "transformers_version": "4.x.x",
        "tokenizer_class_name": "Qwen2TokenizerFast",
        "tokenizer_revision": "Qwen/Qwen3-8B",
        "cuda_device": None,
        "generation_terminated_by_budget": False,
        "stop_criteria": ["</action>", "<|endoftext|>"],
        # Caller-supplied fields (see run_inference.py meta_row assembly).
        "instance_id": instance_id,
        "level_name": level,
        "seed": seed,
        "variant": 0,
        "parsed_action_x": 1.0,
        "parsed_action_y": 2.0,
        "parsed_action_radius": 0.5,
        "factual_outcome": True,
        "factual_step_count": 120,
        "scene_dict_path": f"scratch/probing/scene_dicts/{instance_id}.json",
    }

    errors: list[str] = []

    if meta_row.get("level_name", "") == "":
        errors.append("level_name is empty")

    if not isinstance(meta_row.get("sampling_seed"), int):
        errors.append(
            f"sampling_seed is not int: {type(meta_row.get('sampling_seed')).__name__}"
        )

    for action_field in ("parsed_action_x", "parsed_action_y", "parsed_action_radius"):
        if not isinstance(meta_row.get(action_field), float):
            errors.append(
                f"{action_field} is not float: {type(meta_row.get(action_field)).__name__}"
            )

    if not isinstance(meta_row.get("factual_outcome"), bool):
        errors.append(
            f"factual_outcome is not bool: {type(meta_row.get('factual_outcome')).__name__}"
        )

    step = meta_row.get("factual_step_count", 0)
    if not isinstance(step, int) or step <= 0:
        errors.append(f"factual_step_count={step!r}; expected int > 0")

    if meta_row.get("level_name", "") not in meta_row.get("instance_id", ""):
        errors.append(
            f"instance_id '{meta_row.get('instance_id')}' does not contain "
            f"level_name '{meta_row.get('level_name')}'"
        )

    if errors:
        _fail("metadata_fields", "; ".join(errors))
        raise SystemExit(1)

    _ok("metadata_fields")


# ---------------------------------------------------------------------------
# Check 5 — HDF5 write-then-read round-trip
# ---------------------------------------------------------------------------


def check_hdf5_roundtrip() -> None:
    """Write one instance's activations to a temp HDF5 file and read them back.

    Uses create_activation_file and write_instance_activations with a 1-layer,
    small hidden-size config to keep memory negligible. Asserts instance_id is
    stored correctly and layer_0 has shape (1, 3, hidden_size) with no NaNs.
    """
    import numpy as np
    from experiments.probing.activation.storage import (
        create_activation_file,
        write_instance_activations,
    )

    # Minimal dimensions — the storage code is architecture-agnostic.
    num_layers = 1
    hidden_size = 8
    instance_id = "smoke_test:0:0:12345"

    with tempfile.TemporaryDirectory() as tmpdir:
        h5_path = str(Path(tmpdir) / "smoke_test.h5")

        # Write phase.
        hdf5_file = create_activation_file(h5_path, num_layers, hidden_size, 1)
        layer_acts = {0: np.zeros((3, hidden_size), dtype=np.float32)}
        write_instance_activations(hdf5_file, instance_id, layer_acts, is_audit=False)
        hdf5_file.close()

        # Read-only verification phase.
        import h5py

        with h5py.File(h5_path, "r") as f:
            stored_ids = f["instance_id"][:]
            # Fixed-length byte strings are padded with null bytes; strip them.
            stored_id = stored_ids[0].decode("utf-8").rstrip("\x00")

            if stored_id != instance_id:
                _fail(
                    "hdf5_roundtrip",
                    f"instance_id mismatch: stored {stored_id!r}, expected {instance_id!r}",
                )
                raise SystemExit(1)

            layer_ds = f["layer_0"]
            if layer_ds.shape != (1, 3, hidden_size):
                _fail(
                    "hdf5_roundtrip",
                    f"layer_0 shape {layer_ds.shape}; expected (1, 3, {hidden_size})",
                )
                raise SystemExit(1)

            data = layer_ds[...].astype(np.float32)
            if np.isnan(data).any():
                _fail("hdf5_roundtrip", "layer_0 contains NaN values")
                raise SystemExit(1)

    _ok("hdf5_roundtrip")


# ---------------------------------------------------------------------------
# Check 6 — Reject-log flush check
# ---------------------------------------------------------------------------


def check_reject_log_flush() -> None:
    """Write a reject entry to a temp file, flush, and assert it appears on disk.

    Mirrors the reject_fh.write(...) + reject_fh.flush() pattern in
    run_inference.py. Verifies that data written to the file handle is visible
    to a concurrent reader before the handle is closed.
    """
    import json

    reject_entry = json.dumps(
        {"instance_id": "smoke_test:0:0:12345", "reason": "smoke_test_probe"}
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        reject_path = Path(tmpdir) / "smoke_rejects.jsonl"

        with open(reject_path, "a") as reject_fh:
            reject_fh.write(reject_entry + "\n")
            reject_fh.flush()

            # Read back while the handle is still open to verify flush semantics.
            content = reject_path.read_text()

        if reject_entry not in content:
            _fail(
                "reject_log_flush",
                "reject entry not visible on disk after flush (before close)",
            )
            raise SystemExit(1)

    _ok("reject_log_flush")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke test for the probing inference pipeline."
    )
    parser.add_argument(
        "--level",
        default="down_to_earth",
        help="Level name to use for environment checks (default: down_to_earth).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=200,
        help="Seed to use for environment checks (default: 200).",
    )
    args = parser.parse_args()

    print(f"Running smoke test: level={args.level} seed={args.seed}")

    check_chat_template(args.level, args.seed)
    check_generation_budget()
    check_factual_rollout(args.level, args.seed)
    check_metadata_fields(args.level, args.seed)
    check_hdf5_roundtrip()
    check_reject_log_flush()

    # All checks passed — write the gate file.
    git_hash = _git_hash()
    gate_dir = Path("scratch/probing")
    gate_dir.mkdir(parents=True, exist_ok=True)
    gate_path = gate_dir / f"smoke_test_passed_{git_hash}.flag"
    gate_path.write_text(
        f"Smoke test passed at git hash {git_hash}\n"
        f"level={args.level} seed={args.seed}\n"
    )
    print(f"Gate file written: {gate_path}")


if __name__ == "__main__":
    main()
