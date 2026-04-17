"""
Entry point for §9.2 counterfactual rollout generation.

Reads the metadata JSONL + calibration.json, runs CF rollouts for all
(instance_id, target, direction) combinations, and writes cf_outcomes parquet.

Usage:
    python -m experiments.probing.scripts.run_cf_rollouts \
        --level down_to_earth \
        --split train \
        --model-id Qwen/Qwen3-8B \
        --shard-idx 0 --shard-total 4

CPU-only (Box2D). Run via SLURM.
"""

from __future__ import annotations

import argparse
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

_checkpoint_requested = False


def _handle_preempt(signum, frame) -> None:
    global _checkpoint_requested
    _checkpoint_requested = True


signal.signal(signal.SIGUSR1, _handle_preempt)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate CF rollouts for one level shard.")
    parser.add_argument("--level", required=True)
    parser.add_argument("--split", required=True, choices=["calibration", "train", "eval"])
    parser.add_argument("--model-id", default="Qwen/Qwen3-8B")
    parser.add_argument("--shard-idx", type=int, default=0)
    parser.add_argument("--shard-total", type=int, default=1)
    parser.add_argument("--metadata-dir", default="scratch/probing/activations")
    parser.add_argument("--scene-dicts-dir", default="scratch/probing/scene_dicts")
    parser.add_argument("--calibration-json", default="scratch/probing/calibration.json")
    parser.add_argument("--output-dir", default="scratch/probing/cf_outcomes")
    args = parser.parse_args()

    shard_idx = int(os.environ.get("SHARD_IDX", args.shard_idx))
    shard_total = int(os.environ.get("SHARD_TOTAL", args.shard_total))

    import pandas as pd
    from experiments.probing.simulation.counterfactual import generate_all_cf_outcomes_for_instance
    from experiments.probing.config import PROBING_SIM_CONFIG
    from interphyre.validation import load_valid_level
    from interphyre.environment import InterphyreEnv
    from interphyre.interventions.triggers import on_contact

    safe_model = args.model_id.replace("/", "_")
    # Merge all metadata shards for this level+split.
    meta_dir = Path(args.metadata_dir)
    meta_files = list(meta_dir.glob(f"{safe_model}_{args.level}_{args.split}_shard*.meta.jsonl"))
    if not meta_files:
        logger.error("No metadata files found for %s %s %s", safe_model, args.level, args.split)
        sys.exit(1)

    all_rows = []
    for mf in meta_files:
        with open(mf) as f:
            for line in f:
                row = json.loads(line.strip())
                if row.get("factual_outcome") is not None:
                    all_rows.append(row)

    # Only keep factual-success instances (CF rollouts are conditional on success per §9.6).
    success_rows = [r for r in all_rows if r["factual_outcome"]]
    logger.info("Total factual-success instances for %s/%s: %d", args.level, args.split, len(success_rows))

    # Shard.
    shard_rows = success_rows[
        shard_idx * len(success_rows) // shard_total :
        (shard_idx + 1) * len(success_rows) // shard_total
    ]
    logger.info("Shard %d/%d: %d instances", shard_idx, shard_total, len(shard_rows))

    output_path = (
        Path(args.output_dir)
        / f"{safe_model}_{args.level}_{args.split}_cf_shard{shard_idx:03d}.jsonl"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    checkpoint_path = output_path.with_suffix(".ckpt.json")
    completed_ids: set[str] = set()
    if checkpoint_path.exists():
        with open(checkpoint_path) as f:
            completed_ids = set(json.load(f).get("completed", []))
        logger.info("Resuming: %d instances already done.", len(completed_ids))

    with open(args.calibration_json) as _f:
        calibration_data = json.load(_f)

    with open(str(output_path), "a") as out_fh:
        for row in shard_rows:
            iid = row["instance_id"]
            if iid in completed_ids:
                continue

            # Load scene_dict from JSON sidecar.
            scene_dict_path = row.get("scene_dict_path")
            if not scene_dict_path or not Path(scene_dict_path).exists():
                logger.warning("Missing scene_dict for %s, skipping.", iid)
                completed_ids.add(iid)
                continue

            with open(scene_dict_path) as f:
                scene_dict = json.load(f)

            parsed_action = (
                row["parsed_action_x"],
                row["parsed_action_y"],
                row["parsed_action_radius"],
            )

            # Rebuild env for this instance.
            seed = row["seed"]
            try:
                validated = load_valid_level(
                    args.level, seed=seed, config=PROBING_SIM_CONFIG
                )
                env = InterphyreEnv(validated.level, config=PROBING_SIM_CONFIG, enable_interventions=True)
                env.reset()
                env.place_action(parsed_action)
                trigger = on_contact("red_ball", "green_ball")
                snapshot, branch_step = env.run_until(trigger, max_steps=500)
            except Exception as exc:
                logger.warning("Branch rollout failed for %s: %s", iid, exc)
                completed_ids.add(iid)
                continue

            cf_rows = generate_all_cf_outcomes_for_instance(
                env=env,
                instance_id=iid,
                level_name=args.level,
                calibration_data=calibration_data,
                factual_outcome=row["factual_outcome"],
                branch_snapshot=snapshot,
                scene_dict=scene_dict,
            )

            for cf_row in cf_rows:
                out_fh.write(json.dumps(cf_row) + "\n")
            out_fh.flush()

            completed_ids.add(iid)

            if _checkpoint_requested:
                with open(checkpoint_path, "w") as f:
                    json.dump({"completed": list(completed_ids)}, f)
                logger.info("Checkpoint saved (%d done). Exiting.", len(completed_ids))
                sys.exit(0)

    with open(checkpoint_path, "w") as f:
        json.dump({"completed": list(completed_ids)}, f)

    logger.info("Shard %d complete: %d CF instances written to %s", shard_idx, len(completed_ids), output_path)

    # Inline verification.
    if not output_path.exists():
        logger.error("FAIL: CF output not written: %s", output_path)
        sys.exit(1)

    with open(output_path) as f:
        n_rows = sum(1 for _ in f)
    logger.info("OK: %s written with %d CF rows.", output_path, n_rows)


if __name__ == "__main__":
    main()
