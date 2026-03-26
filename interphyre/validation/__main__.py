"""Command-line interface for interphyre.validation.

Usage:
    python -m interphyre.validation prewarm \\
        --levels basket_case tipping_point \\
        --seeds 0:5000 \\
        --workers 8 \\
        [--registry ~/.cache/interphyre/seed_registry.db] \\
        [--max-variants 10] \\
        [--attempts 50] \\
        [--oracle-steps 500] \\
        [--no-progress]
"""

from __future__ import annotations

import argparse

from interphyre.validation import prewarm
from interphyre.validation.registry import SeedRegistry


def _parse_seeds(seeds_str: str) -> range:
    """Parse 'start:stop' or 'start:stop:step' into a range."""
    parts = seeds_str.split(":")
    try:
        if len(parts) == 2:
            return range(int(parts[0]), int(parts[1]))
        if len(parts) == 3:
            return range(int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        pass
    raise argparse.ArgumentTypeError(
        f"Invalid seeds format '{seeds_str}'. "
        "Expected 'start:stop' or 'start:stop:step' with integer values."
    )


def _print_summary(counts: dict[str, dict[str, int]]) -> None:
    """Print the per-level outcome counts as an aligned table."""
    col_width = max((len(name) for name in counts), default=5)
    header = (
        f"{'Level':<{col_width}}   {'valid':>8}   {'trivial':>8}   "
        f"{'impossible':>10}   {'exhausted':>9}"
    )
    print(header)
    print("-" * len(header))
    for level_name, c in counts.items():
        print(
            f"{level_name:<{col_width}}   {c['valid']:>8}   {c['trivial']:>8}   "
            f"{c['impossible']:>10}   {c['exhausted']:>9}"
        )


def _cmd_prewarm(args: argparse.Namespace) -> None:
    registry = SeedRegistry(args.registry) if args.registry else None
    counts = prewarm(
        level_names=args.levels,
        seeds=args.seeds,
        registry=registry,
        workers=args.workers,
        max_variants=args.max_variants,
        n_attempts=args.attempts,
        oracle_steps=args.oracle_steps,
        progress=not args.no_progress,
    )
    _print_summary(counts)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m interphyre.validation",
        description="Interphyre validation CLI.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    prewarm_p = sub.add_parser(
        "prewarm",
        help="Pre-validate seeds for one or more levels in parallel.",
    )
    prewarm_p.add_argument(
        "--levels",
        nargs="+",
        required=True,
        metavar="LEVEL",
        help="Level names to pre-validate (e.g. basket_case tipping_point).",
    )
    prewarm_p.add_argument(
        "--seeds",
        required=True,
        type=_parse_seeds,
        metavar="START:STOP[:STEP]",
        help="Seed range in Python slice syntax, e.g. '0:5000' or '0:10000:2'.",
    )
    prewarm_p.add_argument(
        "--workers",
        type=int,
        default=4,
        metavar="N",
        help="Number of parallel worker processes (default: 4).",
    )
    prewarm_p.add_argument(
        "--registry",
        default=None,
        metavar="PATH",
        help=(
            "Path to the SQLite registry. "
            "Defaults to ~/.cache/interphyre/seed_registry.db."
        ),
    )
    prewarm_p.add_argument(
        "--max-variants",
        type=int,
        default=10,
        metavar="N",
        help="Max variant attempts per seed before marking exhausted (default: 10).",
    )
    prewarm_p.add_argument(
        "--attempts",
        type=int,
        default=50,
        metavar="N",
        help="Oracle attempts per variant (default: 50).",
    )
    prewarm_p.add_argument(
        "--oracle-steps",
        type=int,
        default=500,
        metavar="N",
        help="Simulation steps per oracle attempt (default: 500).",
    )
    prewarm_p.add_argument(
        "--no-progress",
        action="store_true",
        help="Suppress the progress bar.",
    )

    args = parser.parse_args()
    if args.command == "prewarm":
        _cmd_prewarm(args)


if __name__ == "__main__":
    main()
