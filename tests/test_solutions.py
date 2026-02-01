#!/usr/bin/env python3
"""
Test Solutions for Interphyre Levels

This script tests solutions from a JSON file without rendering,
making it suitable for CI/CD and automated testing.
"""

import argparse
import json
import os
import sys
import time
import pytest
from typing import Dict, List, Any, Tuple, Optional

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from interphyre.levels import load_level
from interphyre.environment import InterphyreEnv
from interphyre.config import SimulationConfig


def run_solution(
    level_name: str, seed: int, action: List, verbose: bool = False
) -> Tuple[bool, Dict[str, Any]]:
    """
    Test a single solution without rendering.

    Args:
        level_name: Name of the level
        seed: Random seed
        action: Solution action to test
        verbose: Whether to print detailed information

    Returns:
        Tuple of (success, info_dict)
    """
    try:
        # Load level
        level = load_level(level_name, seed=seed)

        # Create environment without renderer
        config = SimulationConfig(fps=60, time_step=1 / 60, enable_profiling=False)
        env = InterphyreEnv.from_level(level, config=config)

        # Reset environment
        obs, info = env.reset()

        # Apply action and run full simulation to completion
        start_time = time.perf_counter()
        obs, reward, terminated, truncated, info = env.step(action)
        end_time = time.perf_counter()

        # Check success from the final step result
        success = info.get("success", False)

        # Clean up
        env.close()

        # Prepare result info
        result_info = {
            "level_name": level_name,
            "seed": seed,
            "action": action,
            "success": success,
            "simulation_time": end_time - start_time,
            "steps": info.get("step_count", 0),
            "error": None,
        }

        if verbose:
            print(f"  Tested {level_name} (seed {seed}): {'✓' if success else '✗'}")
            print(f"    Action: {action}")
            print(f"    Simulation time: {result_info['simulation_time']:.3f}s")
            print(f"    Steps: {result_info['steps']}")

        return success, result_info

    except Exception as e:
        error_info = {
            "level_name": level_name,
            "seed": seed,
            "action": action,
            "success": False,
            "simulation_time": 0.0,
            "steps": 0,
            "error": str(e),
        }

        if verbose:
            print(f"  Error testing {level_name} (seed {seed}): {e}")

        return False, error_info


def run_solutions_file(
    solutions_file: str = "solutions.json",
    verbose: bool = False,
    max_tests: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Test all solutions from a JSON file.

    Args:
        solutions_file: Path to the solutions JSON file
        verbose: Whether to print detailed progress
        max_tests: Maximum number of tests to run (for quick testing)

    Returns:
        Dictionary with test results
    """
    # Load solutions
    if not os.path.exists(solutions_file):
        raise FileNotFoundError(f"Solutions file not found: {solutions_file}")

    with open(solutions_file, "r") as f:
        solutions_data = json.load(f)

    print(f"Testing solutions from {solutions_file}")
    print(f"Found {len(solutions_data)} levels")
    print("-" * 60)

    # Collect all tests
    all_tests = []
    for level_name, level_data in solutions_data.items():
        for seed_str, action in level_data["solutions"].items():
            all_tests.append((level_name, int(seed_str), action))

    # Limit tests if requested
    if max_tests and len(all_tests) > max_tests:
        all_tests = all_tests[:max_tests]
        print(f"Limited to {max_tests} tests for quick testing")

    print(f"Running {len(all_tests)} tests...")
    print()

    # Run tests
    results = {
        "total_tests": len(all_tests),
        "passed_tests": 0,
        "failed_tests": 0,
        "error_tests": 0,
        "level_results": {},
        "test_details": [],
    }

    start_time = time.perf_counter()

    for i, (level_name, seed, action) in enumerate(all_tests, 1):
        if verbose:
            print(f"Test {i}/{len(all_tests)}: {level_name} (seed {seed})")

        success, test_info = run_solution(level_name, seed, action, verbose=verbose)

        # Update counters
        if test_info["error"]:
            results["error_tests"] += 1
        elif success:
            results["passed_tests"] += 1
        else:
            results["failed_tests"] += 1

        # Store test details
        results["test_details"].append(test_info)

        # Update level results
        if level_name not in results["level_results"]:
            results["level_results"][level_name] = {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0,
            }

        level_result = results["level_results"][level_name]
        level_result["total"] += 1
        if test_info["error"]:
            level_result["errors"] += 1
        elif success:
            level_result["passed"] += 1
        else:
            level_result["failed"] += 1

    end_time = time.perf_counter()
    results["total_time"] = end_time - start_time

    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['failed_tests']}")
    print(f"Errors: {results['error_tests']}")
    print(f"Success rate: {results['passed_tests']/results['total_tests']*100:.1f}%")
    print(f"Total time: {results['total_time']:.3f}s")
    print(f"Average time per test: {results['total_time']/results['total_tests']:.3f}s")

    print(f"\nLevel-by-level results:")
    for level_name, level_result in results["level_results"].items():
        success_rate = level_result["passed"] / level_result["total"] * 100
        print(
            f"  {level_name}: {level_result['passed']}/{level_result['total']} ({success_rate:.1f}%)"
        )

    # Print failed tests if any
    failed_tests = [
        test
        for test in results["test_details"]
        if not test["success"] and not test["error"]
    ]
    if failed_tests:
        print(f"\nFailed tests:")
        for test in failed_tests:
            print(f"  {test['level_name']} (seed {test['seed']}): {test['action']}")

    # Print error tests if any
    error_tests = [test for test in results["test_details"] if test["error"]]
    if error_tests:
        print(f"\nError tests:")
        for test in error_tests:
            print(f"  {test['level_name']} (seed {test['seed']}): {test['error']}")

    return results


def test_solutions_file_default():
    """Run solution tests against the bundled test solutions file."""
    solutions_path = os.path.join(os.path.dirname(__file__), "test_solutions.json")
    if not os.path.exists(solutions_path):
        pytest.skip(f"Solutions file not found: {solutions_path}")
    run_solutions_file(solutions_file=solutions_path, max_tests=10)


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Test solutions for Interphyre levels")
    parser.add_argument(
        "--solutions",
        type=str,
        default="solutions.json",
        help="Path to solutions JSON file (default: solutions.json)",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--max-tests",
        type=int,
        help="Maximum number of tests to run (for quick testing)",
    )
    parser.add_argument("--output", type=str, help="Save detailed results to JSON file")

    args = parser.parse_args()

    try:
        results = run_solutions_file(
            solutions_file=args.solutions,
            verbose=args.verbose,
            max_tests=args.max_tests,
        )

        # Save results if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\nDetailed results saved to {args.output}")

        # Exit with error code if any tests failed
        if results["failed_tests"] > 0 or results["error_tests"] > 0:
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
