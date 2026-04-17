"""
Repair factual_outcome labels in completed inference metadata.

The original run_inference.py stopped the factual rollout at on_contact("red_ball",
"green_ball") and checked env.success at the branch point — too early. The puzzle
requires more simulation steps after that contact to reach the success condition.
This script re-runs the full factual rollout (to on_success) for each completed
instance and rewrites the meta.jsonl files with correct factual_outcome values.

Usage:
    python -m experiments.probing.scripts.repair_factual_outcomes \
        --activations-dir scratch/probing/activations \
        --model-id Qwen/Qwen3-8B

Safe to re-run: reads checkpoint files to identify completed shards, skips
instances whose meta row already has correct factual_outcome (by re-verifying).
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)


def repair_shard_meta(meta_path: Path, config) -> tuple[int, int]:
    """Re-run factual rollouts and rewrite meta.jsonl. Returns (n_fixed, n_total)."""
    from interphyre.validation import load_valid_level
    from interphyre.environment import InterphyreEnv
    from interphyre.interventions.triggers import on_success

    rows = [json.loads(l) for l in meta_path.open()]
    n_fixed = 0

    for row in rows:
        seed = row["seed"]
        px = row["parsed_action_x"]
        py = row["parsed_action_y"]
        pr = row["parsed_action_radius"]
        # level_name was stored as "" in shards affected by the metadata spread
        # bug; recover it from the instance_id or the shard filename.
        level_name = row.get("level_name") or ""
        if not level_name:
            # instance_id format: <level>:<seed>:<variant>:<sampling_seed>
            iid = row.get("instance_id", "")
            level_name = iid.split(":")[0] if ":" in iid else ""
        if not level_name:
            # Fall back to shard filename: ..._<level>_<split>_shard...
            stem = meta_path.stem  # e.g. Qwen_Qwen3-8B_down_to_earth_train_shard001
            parts = stem.replace("Qwen_Qwen3-8B_", "").rsplit("_shard", 1)[0]
            # parts = "down_to_earth_train"; level is everything before the last _word
            level_name = "_".join(parts.split("_")[:-1])

        try:
            validated = load_valid_level(level_name, seed=seed, config=config)
            env = InterphyreEnv(validated.level, config=config, enable_interventions=True)
            env.reset()
            env.place_action((px, py, pr))
            env.run_until(on_success(), max_steps=500)
            correct_outcome = env._level.success_condition(env.engine)
            correct_step_count = env.describe_scene()["step_count"]
        except Exception as exc:
            logger.warning("Repair rollout failed seed=%d: %s", seed, exc)
            continue

        if row["factual_outcome"] != correct_outcome:
            n_fixed += 1
            logger.info("Fixed seed=%d: %s → %s", seed, row["factual_outcome"], correct_outcome)
        row["factual_outcome"] = bool(correct_outcome)
        row["factual_step_count"] = int(correct_step_count)
        # Also fix level_name="" left by the metadata-spread bug.
        if not row.get("level_name"):
            row["level_name"] = level_name

    # Rewrite the meta file atomically.
    tmp = meta_path.with_suffix(".jsonl.tmp")
    with tmp.open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    tmp.rename(meta_path)
    return n_fixed, len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--activations-dir", default="scratch/probing/activations")
    parser.add_argument("--model-id", default="Qwen/Qwen3-8B")
    args = parser.parse_args()

    from experiments.probing.config import PROBING_SIM_CONFIG

    safe_model = args.model_id.replace("/", "_")
    acts_dir = Path(args.activations_dir)

    # Find all completed shards: have a .ckpt.json with 25 completed seeds.
    completed_meta = []
    for ckpt in sorted(acts_dir.glob(f"{safe_model}_*.ckpt.json")):
        data = json.loads(ckpt.read_text())
        if len(data.get("completed_seeds", [])) == 25:
            meta = ckpt.with_suffix("").with_suffix(".meta.jsonl")
            if meta.exists():
                completed_meta.append(meta)

    logger.info("Found %d completed shards to repair.", len(completed_meta))
    total_fixed = total_rows = 0

    for meta_path in completed_meta:
        logger.info("Repairing %s ...", meta_path.name)
        n_fixed, n_rows = repair_shard_meta(meta_path, PROBING_SIM_CONFIG)
        total_fixed += n_fixed
        total_rows += n_rows
        logger.info("  %d/%d rows had wrong factual_outcome", n_fixed, n_rows)

    logger.info("Done. Fixed %d/%d rows across %d shards.", total_fixed, total_rows, len(completed_meta))


if __name__ == "__main__":
    main()
