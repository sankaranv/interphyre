#!/usr/bin/env python3
"""
Test data determinism - verify that solutions produce consistent results.

This tool tests whether actions produce the same success/failure result
across multiple runs, helping identify non-determinism issues in the
physics simulation or contact tracking.

Usage:
    # Test a specific solution
    python tools/test_data_determinism.py --level cliffhanger --seed 42 \\
        --action "3.6201,2.8675,0.7744" --runs 20

    # Test all solutions in a file
    python tools/test_data_determinism.py --solutions tests/solutions/successes.json \\
        --runs 10

    # Test with detailed output
    python tools/test_data_determinism.py --solutions tests/solutions/successes.json \\
        --runs 20 --verbose
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Tuple, Optional

from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from interphyre.environment import PhyreEnv
from interphyre.config import SimulationConfig
from interphyre.levels import load_level


def test_solution_determinism(
    level_name: str,
    seed: int,
    action: List[float],
    num_runs: int = 10,
    verbose: bool = False,
) -> Tuple[bool, List[bool], List[str]]:
    """Verify that an action produces consistent results across runs.

    Args:
        level_name: Name of the level
        seed: Random seed
        action: Action as list of [x, y, radius, ...] values
        num_runs: Number of times to run the action
        verbose: If True, print detailed information

    Returns:
        Tuple of (is_deterministic, results_list, error_messages)
    """
    # Convert flat action list to tuples
    if len(action) % 3 != 0:
        return False, [], [f"Invalid action length: {len(action)} (must be multiple of 3)"]

    action_tuples = [
        (float(action[i]), float(action[i + 1]), float(action[i + 2]))
        for i in range(0, len(action), 3)
    ]

    results = []
    errors = []

    for run_idx in range(num_runs):
        try:
            # Create fresh environment for each run
            level = load_level(level_name, seed=seed)
            env = PhyreEnv(
                level=level,
                config=SimulationConfig(max_steps=1000),
                observation_type="physics_state",
                action_type="continuous",
                discrete_colors=False,
            )

            # Run simulation
            env.reset(seed=seed)
            _, _, _, _, info = env.step(action_tuples)
            success = bool(info.get("success", False))
            results.append(success)
            env.close()

            if verbose and run_idx == 0:
                print(f"  Run 1: {'SUCCESS' if success else 'FAILURE'}")

        except Exception as e:
            errors.append(f"Run {run_idx + 1} failed: {str(e)}")
            results.append(None)

    # Check if all results are the same
    unique_results = set(r for r in results if r is not None)

    if len(unique_results) > 1:
        return False, results, errors

    if len(unique_results) == 0:
        return False, results, errors + ["All runs failed"]

    return True, results, errors


def test_all_solutions(
    solutions_file: Path,
    num_runs: int = 10,
    verbose: bool = False,
) -> dict:
    """Test all solutions in a file for determinism.

    Args:
        solutions_file: Path to solutions JSON file
        num_runs: Number of runs per solution
        verbose: If True, print detailed information

    Returns:
        Dictionary with test results
    """
    with open(solutions_file) as f:
        data = json.load(f)

    print(f"Testing solutions from {solutions_file.name}")
    print(f"Running each solution {num_runs} times...\n")

    total_solutions = 0
    deterministic_count = 0
    non_deterministic = []

    for level_name, level_data in data.items():
        if level_name.startswith("_"):  # Skip metadata keys like "_note"
            continue

        if "solutions" not in level_data:
            continue

        solutions = level_data["solutions"]
        print(f"\n{level_name}:")

        level_pbar = tqdm(
            solutions.items(),
            desc=f"  {level_name}",
            unit="seed",
            leave=False,
            file=sys.stderr,
        )

        for seed_str, actions_list in level_pbar:
            seed = int(seed_str)

            # actions_list is typically [[x, y, r], ...] or a flat list
            if isinstance(actions_list[0], list):
                # Flatten nested list
                action = [x for triplet in actions_list for x in triplet]
            else:
                action = actions_list

            total_solutions += 1

            is_deterministic, results, errors = test_solution_determinism(
                level_name, seed, action, num_runs, verbose
            )

            if is_deterministic:
                deterministic_count += 1
                if verbose:
                    print(f"  Seed {seed}: ✓ DETERMINISTIC ({results[0]})")
            else:
                non_deterministic.append((level_name, seed, results, errors))
                unique_results = set(r for r in results if r is not None)
                print(f"  Seed {seed}: ✗ NON-DETERMINISTIC - results: {unique_results}")
                if errors:
                    print(f"    Errors: {errors}")

        level_pbar.close()

    print(f"\n{'='*60}")
    print("SUMMARY:")
    print(f"  Total solutions tested: {total_solutions}")
    print(f"  Deterministic: {deterministic_count} ({deterministic_count/total_solutions*100:.1f}%)")
    print(f"  Non-deterministic: {len(non_deterministic)} ({len(non_deterministic)/total_solutions*100:.1f}%)")

    if non_deterministic:
        print(f"\nNon-deterministic solutions (first 10):")
        for level_name, seed, results, errors in non_deterministic[:10]:
            unique_results = set(r for r in results if r is not None)
            print(f"  {level_name} seed {seed}: {unique_results}")

    return {
        "total": total_solutions,
        "deterministic": deterministic_count,
        "non_deterministic": len(non_deterministic),
        "non_deterministic_details": non_deterministic,
    }


def test_specific_action(
    level_name: str,
    seed: int,
    action_str: str,
    num_runs: int = 10,
    verbose: bool = True,
) -> bool:
    """Test a specific action for determinism.

    Args:
        level_name: Level name
        seed: Random seed
        action_str: Action as comma-separated string (e.g., "3.6,2.8,0.7")
        num_runs: Number of runs
        verbose: If True, print detailed information

    Returns:
        True if action is deterministic
    """
    # Parse action string
    try:
        action = [float(x.strip()) for x in action_str.split(",")]
    except ValueError as e:
        print(f"Error parsing action: {e}")
        return False

    print(f"Testing {level_name} seed {seed} with action {action}")
    print(f"Running {num_runs} times...\n")

    is_deterministic, results, errors = test_solution_determinism(
        level_name, seed, action, num_runs, verbose
    )

    if is_deterministic:
        print(f"\n✓ ACTION IS DETERMINISTIC")
        print(f"  All {num_runs} runs produced: {results[0]}")
        return True
    else:
        print(f"\n✗ ACTION IS NOT DETERMINISTIC")
        unique_results = set(r for r in results if r is not None)
        print(f"  Unique results: {unique_results}")
        print(f"  Distribution:")
        for result in unique_results:
            count = sum(1 for r in results if r == result)
            print(f"    {result}: {count}/{num_runs} runs")

        if errors:
            print(f"  Errors:")
            for error in errors[:5]:
                print(f"    {error}")

        return False


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        description="Test solution determinism",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Test mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--solutions",
        type=Path,
        help="Path to solutions JSON file to test all solutions",
    )
    mode_group.add_argument(
        "--level",
        type=str,
        help="Level name (use with --seed and --action for single test)",
    )

    # Single action test parameters
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed (required with --level)",
    )
    parser.add_argument(
        "--action",
        type=str,
        help='Action as comma-separated values (e.g., "3.6,2.8,0.7")',
    )

    # Common parameters
    parser.add_argument(
        "--runs",
        type=int,
        default=10,
        help="Number of runs per solution (default: 10)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    return parser


def main() -> None:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.solutions:
        # Test all solutions in file
        if not args.solutions.exists():
            print(f"Error: File not found: {args.solutions}")
            sys.exit(1)

        results = test_all_solutions(args.solutions, args.runs, args.verbose)

        # Exit with error code if any non-deterministic solutions found
        if results["non_deterministic"] > 0:
            sys.exit(1)

    else:
        # Test specific action
        if not args.seed or not args.action:
            print("Error: --seed and --action required with --level")
            parser.print_help()
            sys.exit(1)

        is_deterministic = test_specific_action(
            args.level, args.seed, args.action, args.runs, args.verbose
        )

        if not is_deterministic:
            sys.exit(1)


if __name__ == "__main__":
    main()
