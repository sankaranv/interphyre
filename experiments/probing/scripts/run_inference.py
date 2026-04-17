"""
Entry point for §10+11 LLM inference + activation extraction for one level shard.

Loads a model, runs inference on a seed range, extracts residual-stream activations
at T1/T2/T3 token positions, and writes results to scratch/.

Usage (standalone):
    python -m experiments.probing.scripts.run_inference \
        --level down_to_earth \
        --split train \
        --model-id Qwen/Qwen3-8B \
        --shard-idx 0 --shard-total 10 \
        --activations-dir scratch/probing/activations \
        --metadata-dir scratch/probing/activations \
        --scene-dicts-dir scratch/probing/scene_dicts

Environment variables (from SLURM array):
    SHARD_IDX, SHARD_TOTAL — override --shard-idx / --shard-total if set.

GPU required. Run via SLURM.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import signal
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Graceful preemption — set flag on SIGUSR1, save checkpoint on next iteration boundary.
_checkpoint_requested = False


def _handle_preempt(signum, frame) -> None:
    global _checkpoint_requested
    _checkpoint_requested = True


signal.signal(signal.SIGUSR1, _handle_preempt)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run LLM inference + activation extraction for one level shard."
    )
    parser.add_argument("--level", required=True)
    parser.add_argument(
        "--split",
        required=True,
        choices=["calibration", "train", "eval"],
        help="Which seed partition to process.",
    )
    parser.add_argument(
        "--model-id",
        default="Qwen/Qwen3-8B",
        help="HuggingFace model ID.",
    )
    parser.add_argument("--shard-idx", type=int, default=0)
    parser.add_argument("--shard-total", type=int, default=1)
    parser.add_argument("--activations-dir", default="scratch/probing/activations")
    parser.add_argument("--metadata-dir", default="scratch/probing/activations")
    parser.add_argument("--scene-dicts-dir", default="scratch/probing/scene_dicts")
    args = parser.parse_args()

    # SLURM array overrides.
    shard_idx = int(os.environ.get("SHARD_IDX", args.shard_idx))
    shard_total = int(os.environ.get("SHARD_TOTAL", args.shard_total))

    from experiments.probing.config import (
        CALIBRATION_SEED_SLICE,
        TRAIN_SEED_SLICE,
        EVAL_SEED_SLICE,
        QWEN3_8B_NUM_LAYERS,
        QWEN3_8B_HIDDEN_SIZE,
        GEMMA2_9B_NUM_LAYERS,
        GEMMA2_9B_HIDDEN_SIZE,
        AUDIT_FRACTION,
    )

    split_map = {
        "calibration": CALIBRATION_SEED_SLICE,
        "train": TRAIN_SEED_SLICE,
        "eval": EVAL_SEED_SLICE,
    }
    all_seed_indices = list(range(*split_map[args.split].indices(10_001)))

    # Shard the seed list.
    shard_seeds = all_seed_indices[
        shard_idx * len(all_seed_indices) // shard_total :
        (shard_idx + 1) * len(all_seed_indices) // shard_total
    ]
    logger.info(
        "Shard %d/%d: level=%s split=%s seeds=%d",
        shard_idx, shard_total, args.level, args.split, len(shard_seeds),
    )

    # Determine architecture constants from model ID.
    if "qwen" in args.model_id.lower():
        num_layers = QWEN3_8B_NUM_LAYERS
        hidden_size = QWEN3_8B_HIDDEN_SIZE
    else:
        num_layers = GEMMA2_9B_NUM_LAYERS
        hidden_size = GEMMA2_9B_HIDDEN_SIZE

    safe_model_id = args.model_id.replace("/", "_")
    output_h5 = (
        Path(args.activations_dir)
        / f"{safe_model_id}_{args.level}_{args.split}_shard{shard_idx:03d}.h5"
    )
    output_meta_path = (
        Path(args.metadata_dir)
        / f"{safe_model_id}_{args.level}_{args.split}_shard{shard_idx:03d}.meta.jsonl"
    )
    reject_log_path = (
        Path(args.activations_dir)
        / f"{safe_model_id}_{args.level}_{args.split}_shard{shard_idx:03d}.rejects.jsonl"
    )
    checkpoint_path = (
        Path(args.activations_dir)
        / f"{safe_model_id}_{args.level}_{args.split}_shard{shard_idx:03d}.ckpt.json"
    )

    for p in [output_h5.parent, output_meta_path.parent, reject_log_path.parent]:
        p.mkdir(parents=True, exist_ok=True)
    Path(args.scene_dicts_dir).mkdir(parents=True, exist_ok=True)

    # Resume from checkpoint if available.
    completed_seeds: set[int] = set()
    if checkpoint_path.exists():
        with open(checkpoint_path) as f:
            completed_seeds = set(json.load(f).get("completed_seeds", []))
        logger.info("Resuming: %d seeds already done", len(completed_seeds))

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, __version__ as tf_version
    from interphyre.validation import load_valid_level
    from interphyre.environment import InterphyreEnv
    from interphyre.interventions.triggers import on_contact
    from experiments.probing.config import PROBING_SIM_CONFIG
    from experiments.probing.inference.runner import (
        load_model_and_tokenizer,
        run_inference_for_instance,
    )
    from experiments.probing.inference.sampling import sampling_seed_for
    from experiments.probing.inference.prompts import render_prompt
    from experiments.probing.activation.extractor import (
        extract_activations_for_instance,
        select_audit_instances,
    )
    from experiments.probing.activation.storage import (
        create_activation_file,
        write_instance_activations,
    )

    # Load model once.
    logger.info("Loading model: %s", args.model_id)
    model, tokenizer = load_model_and_tokenizer(args.model_id)
    device = next(model.parameters()).device
    logger.info(
        "Model loaded. Device=%s, dtype=%s, transformers=%s",
        device, next(model.parameters()).dtype, tf_version,
    )

    layer_indices = list(range(num_layers))
    audit_ids = select_audit_instances(
        [
            f"{args.level}:{s}:0:{sampling_seed_for(args.level, s, 0, args.model_id)}"
            for s in shard_seeds
        ],
        AUDIT_FRACTION,
    )

    # If a previous job was cancelled mid-write, the HDF5 may carry a stale SWMR
    # write-lock flag that prevents reopening in append mode. Detect this by
    # attempting a read-only open; on failure, delete both the HDF5 and the
    # checkpoint so the shard restarts cleanly from seed 0.
    if output_h5.exists():
        import h5py as _h5py_check
        try:
            with _h5py_check.File(str(output_h5), "r"):
                pass
        except OSError:
            logger.warning(
                "HDF5 %s has stale SWMR lock; deleting and restarting shard.", output_h5
            )
            output_h5.unlink()
            if checkpoint_path.exists():
                checkpoint_path.unlink()
            completed_seeds = set()

    hdf5_file = create_activation_file(
        str(output_h5), num_layers, hidden_size, len(shard_seeds)
    )
    meta_fh = open(output_meta_path, "a")
    reject_fh = open(reject_log_path, "a")

    try:
        for seed_idx in shard_seeds:
            if seed_idx in completed_seeds:
                continue

            # Provisional instance_id (variant=unknown) used only if load_valid_level fails.
            samp_seed = sampling_seed_for(args.level, seed_idx, 0, args.model_id)
            instance_id = f"{args.level}:{seed_idx}:unknown:{samp_seed}"

            # Load level and build prompt.
            try:
                validated = load_valid_level(
                    args.level, seed=seed_idx, config=PROBING_SIM_CONFIG
                )
                instance_id = f"{args.level}:{seed_idx}:{validated.variant}:{samp_seed}"
                env = InterphyreEnv(validated.level, config=PROBING_SIM_CONFIG, enable_interventions=True)
                env.reset()
                scene_dict = env.describe_scene()
                prompt_text = render_prompt(scene_dict, args.level)
            except Exception as exc:
                logger.warning("Level load failed seed=%d: %s", seed_idx, exc)
                reject_fh.write(json.dumps({"instance_id": instance_id, "reason": f"level_load: {exc}"}) + "\n")
                reject_fh.flush()
                completed_seeds.add(seed_idx)
                continue

            # Write scene_dict JSON.
            scene_dict_path = Path(args.scene_dicts_dir) / f"{instance_id}.json"
            scene_dict_path.write_text(json.dumps(scene_dict))

            # Run inference.
            logger.info("seed=%d: starting inference", seed_idx)
            inf_result = run_inference_for_instance(
                model, tokenizer, args.model_id, prompt_text, samp_seed
            )
            n_gen = len(inf_result["output_ids"])
            logger.info(
                "seed=%d: inference done, %d tokens, budget=%s, parsed=%s",
                seed_idx, n_gen, inf_result["terminated_by_budget"],
                inf_result["parsed_action"] is not None,
            )

            if inf_result["parsed_action"] is None:
                reject_fh.write(
                    json.dumps({
                        "instance_id": instance_id,
                        "reason": "parse_failure",
                        "output_text": inf_result["output_text"][:500],
                    }) + "\n"
                )
                reject_fh.flush()
                completed_seeds.add(seed_idx)
                continue

            # Run factual simulation to get factual outcome.
            px, py, pr = inf_result["parsed_action"]
            try:
                env.reset()
                env.place_action((px, py, pr))
                trigger = on_contact("red_ball", "green_ball")
                snapshot, branch_step = env.run_until(trigger, max_steps=500)
                factual_outcome = env.success
                factual_step_count = env.describe_scene()["step_count"]
            except Exception as exc:
                logger.warning("Factual rollout failed seed=%d: %s", seed_idx, exc)
                reject_fh.write(json.dumps({"instance_id": instance_id, "reason": f"rollout: {exc}"}) + "\n")
                reject_fh.flush()
                completed_seeds.add(seed_idx)
                continue

            # Extract activations.
            act_result = extract_activations_for_instance(
                model, tokenizer, args.model_id,
                inf_result["output_text"], inf_result["output_ids"],
                layer_indices, hidden_size,
            )

            if act_result is None:
                reject_fh.write(json.dumps({"instance_id": instance_id, "reason": "activation_extraction_failed"}) + "\n")
                reject_fh.flush()
                completed_seeds.add(seed_idx)
                continue

            # Write to HDF5.
            is_audit = instance_id in audit_ids
            import numpy as np
            layer_acts = {
                L: act_result[L].astype(np.float32) for L in act_result
            }
            write_instance_activations(hdf5_file, instance_id, layer_acts, is_audit=is_audit)

            # Write metadata row.
            meta_row = {
                "instance_id": instance_id,
                "level_name": args.level,
                "seed": seed_idx,
                "variant": 0,
                "sampling_seed": samp_seed,
                "parsed_action_x": px,
                "parsed_action_y": py,
                "parsed_action_radius": pr,
                "factual_outcome": bool(factual_outcome),
                "factual_step_count": int(factual_step_count),
                "scene_dict_path": str(scene_dict_path),
                **inf_result["inference_metadata"],
            }
            meta_fh.write(json.dumps(meta_row) + "\n")
            meta_fh.flush()

            completed_seeds.add(seed_idx)

            # Save checkpoint on preemption signal.
            if _checkpoint_requested:
                with open(checkpoint_path, "w") as f:
                    json.dump({"completed_seeds": list(completed_seeds)}, f)
                logger.info("Checkpoint saved (%d done). Exiting for requeue.", len(completed_seeds))
                sys.exit(0)

    finally:
        hdf5_file.close()
        meta_fh.close()
        reject_fh.close()
        # Save checkpoint on clean exit too.
        with open(checkpoint_path, "w") as f:
            json.dump({"completed_seeds": list(completed_seeds)}, f)

    logger.info("Shard %d complete. %d seeds processed.", shard_idx, len(completed_seeds))

    # Inline verification.
    if not output_h5.exists():
        logger.error("FAIL: HDF5 output not written: %s", output_h5)
        sys.exit(1)
    import h5py
    with h5py.File(str(output_h5), "r") as f:
        n_written = len(f["instance_id"])
    logger.info("OK: %s written with %d instances.", output_h5, n_written)


if __name__ == "__main__":
    main()
