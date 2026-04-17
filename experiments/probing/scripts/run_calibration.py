"""
Entry point for §9.4 magnitude calibration.

Runs calibration for one level (specified via --level) using 200 calibration seeds
(indices 0–199 from the level bundle). Writes results to scratch/probing/calibration.json.

Usage:
    python -m experiments.probing.scripts.run_calibration --level down_to_earth

Run via SLURM (CPU-only) — not on login node.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run §9.4 magnitude calibration for one level.")
    parser.add_argument(
        "--level",
        required=True,
        choices=["down_to_earth", "end_of_line", "two_body_problem", "keyhole", "mind_the_gap", "zebra_crossing"],
    )
    parser.add_argument(
        "--output-json",
        default="scratch/probing/calibration.json",
        help="Path to calibration.json (merged-write).",
    )
    args = parser.parse_args()

    from experiments.probing.config import (
        CALIBRATION_SEED_SLICE,
        PRIMARY_LEVELS,
        FALLBACK_LEVEL,
    )
    from experiments.probing.simulation.calibration import run_calibration_for_level
    from interphyre.validation import load_valid_level

    # Enumerate calibration seeds (0-indexed into the level bundle).
    seed_indices = list(range(CALIBRATION_SEED_SLICE.start, CALIBRATION_SEED_SLICE.stop))
    logger.info(
        "Starting calibration: level=%s, n_seeds=%d", args.level, len(seed_indices)
    )

    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)

    result = run_calibration_for_level(
        level_name=args.level,
        seed_indices=seed_indices,
        calibration_json_path=args.output_json,
    )

    # Print summary for log.
    dropped = [
        f"{t}/{d}"
        for t, dirs in result.items()
        for d, v in dirs.items()
        if v is None
    ]
    logger.info(
        "Calibration complete: %s. Dropped combinations: %s",
        args.level,
        dropped if dropped else "none",
    )

    # Verify output exists and is valid JSON.
    if not Path(args.output_json).exists():
        logger.error("calibration.json not written. Exiting with error.")
        sys.exit(1)

    with open(args.output_json) as f:
        data = json.load(f)
    assert args.level in data, f"Level {args.level} not in calibration.json after write."
    logger.info("Verification OK: %s present in %s", args.level, args.output_json)


if __name__ == "__main__":
    main()
