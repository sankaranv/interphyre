#!/usr/bin/env python3
"""Stress-test levels for trivial/unstable solutions.

A level is *trivially solved* if the success condition fires without any
action objects placed — i.e., the non-action scene physics alone reaches
the goal state.  This catches:

  - Objects that overlap at spawn and immediately satisfy the contact condition
  - Dynamic objects that drift/fall into the goal region under gravity alone
  - Marginal physics instabilities that accumulate into a false positive

Usage
-----
    python tests/stress/level_stability.py                      # all two-ball levels, 100 seeds
    python tests/stress/level_stability.py --levels task00120   # single level
    python tests/stress/level_stability.py --seeds 200 --steps 600
    python tests/stress/level_stability.py --verbose            # show per-seed detail

Exit code 0 = all levels stable; 1 = at least one trivial seed found.
"""

import argparse
import sys

from interphyre.config import SimulationConfig
from interphyre.engine import Box2DEngine
from interphyre.levels import load_level

TWO_BALL_LEVELS = [f"task{i:05d}" for i in range(100, 125)]


def _null_simulate(level_name: str, seed: int, config: SimulationConfig, max_steps: int) -> int | None:
    """Run physics without action objects. Returns the step where success fires, or None."""
    level = load_level(level_name, seed=seed)
    engine = Box2DEngine(level=level, config=config)
    for step in range(max_steps):
        engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
        engine.time_update(config.time_step)
        if level.success_condition(engine):
            return step
    return None


def check_level(
    level_name: str,
    n_seeds: int,
    max_steps: int,
    config: SimulationConfig,
    verbose: bool = False,
) -> dict:
    """Sweep n_seeds for trivial solutions. Returns summary dict."""
    trivial = []   # (seed, step) pairs where success fired without action objects
    errors = []    # (seed, exc) pairs for seeds that raised

    for seed in range(n_seeds):
        try:
            trigger_step = _null_simulate(level_name, seed, config, max_steps)
        except Exception as exc:
            errors.append((seed, exc))
            continue

        if trigger_step is not None:
            trivial.append((seed, trigger_step))
            if verbose:
                print(f"  [TRIVIAL] seed={seed:4d}  step={trigger_step:4d} ({trigger_step * config.time_step:.2f}s)")

    return {"trivial": trivial, "errors": errors, "n_seeds": n_seeds}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stress-test levels for trivial/unstable solutions (no action objects).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage")[0].strip(),
    )
    parser.add_argument(
        "--levels",
        nargs="*",
        default=TWO_BALL_LEVELS,
        metavar="LEVEL",
        help="Level names to test (default: all two-ball levels task00100–task00124)",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        default=100,
        metavar="N",
        help="Number of seeds to test per level (default: 100)",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=300,
        metavar="N",
        help="Max physics steps per seed (default: 300 ≈ 5s at 60fps)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print every trivial seed as it is found",
    )
    args = parser.parse_args()

    config = SimulationConfig()
    sim_duration = args.steps * config.time_step

    print(
        f"Null-simulation stability check\n"
        f"  levels : {len(args.levels)}\n"
        f"  seeds  : {args.seeds} per level\n"
        f"  horizon: {args.steps} steps ({sim_duration:.1f}s)\n"
    )

    any_failures = False
    col = max(len(n) for n in args.levels) + 2

    for level_name in args.levels:
        if args.verbose:
            print(f"{level_name}:")
        result = check_level(level_name, args.seeds, args.steps, config, verbose=args.verbose)

        n_trivial = len(result["trivial"])
        n_errors = len(result["errors"])
        pct = 100 * n_trivial / result["n_seeds"]
        status = "OK  " if n_trivial == 0 and n_errors == 0 else "FAIL"
        if status == "FAIL":
            any_failures = True

        line = f"{level_name:<{col}}[{status}]  trivial={n_trivial}/{args.seeds} ({pct:4.1f}%)"
        if n_errors:
            line += f"  errors={n_errors}"
        print(line)

        if not args.verbose and result["trivial"]:
            # Show up to 3 examples inline
            for seed, step in result["trivial"][:3]:
                print(f"  seed={seed:4d}  step={step:4d} ({step * config.time_step:.2f}s)")
            if n_trivial > 3:
                print(f"  ... and {n_trivial - 3} more")

        if result["errors"]:
            for seed, exc in result["errors"][:2]:
                print(f"  seed={seed:4d}  error: {exc}")

    print()
    if any_failures:
        print("RESULT: failures found — see FAIL rows above")
    else:
        print("RESULT: all levels stable across all seeds")

    return 1 if any_failures else 0


if __name__ == "__main__":
    sys.exit(main())
