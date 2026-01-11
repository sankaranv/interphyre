#!/usr/bin/env python3
"""
Run collect_data.py across all levels with a shared set of arguments.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def get_level_names() -> List[str]:
    levels_dir = PROJECT_ROOT / "interphyre" / "levels"
    names = []
    for entry in os.listdir(levels_dir):
        path = levels_dir / entry
        if path.is_file() and entry.endswith(".py") and entry != "__init__.py":
            names.append(entry[:-3])
    return sorted(names)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run tools/collect_data.py across all levels"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/",
        help="Output directory for collected data",
    )
    parser.add_argument(
        "--seeds",
        required=True,
        help="Comma-separated list of seeds",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of workers to pass through",
    )
    parser.add_argument(
        "--agent",
        choices=["random", "cem"],
        default="cem",
        help="Agent to use for success search",
    )
    parser.add_argument(
        "--cem-population",
        type=int,
        default=128,
        help="CEM population size per iteration",
    )
    parser.add_argument(
        "--cem-iterations",
        type=int,
        default=5,
        help="CEM iterations per attempt",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=400,
        help="Max attempts per seed",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing solutions",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    levels = get_level_names()
    if not levels:
        print("No levels found.", file=sys.stderr)
        sys.exit(1)

    no_overwrite = not args.overwrite

    failures = []
    for level in levels:
        cmd = [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "collect_data.py"),
            "--level",
            level,
            "--output-dir",
            args.output_dir,
            "--seeds",
            args.seeds,
            "--workers",
            str(args.workers),
            "--agent",
            args.agent,
            "--cem-population",
            str(args.cem_population),
            "--cem-iterations",
            str(args.cem_iterations),
            "--max-attempts",
            str(args.max_attempts),
        ]
        if no_overwrite:
            cmd.append("--no-overwrite")

        print(f"\n=== {level} ===", file=sys.stderr)
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            failures.append(level)

    if failures:
        print(
            "Failed levels: " + ", ".join(failures),
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
