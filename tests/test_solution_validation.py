"""
Test solution validation - ensure successes succeed and failures fail.

This test file validates that:
1. Solutions in solutions/successes.json achieve success
2. Solutions in solutions/failures.json result in failure

This is a regression test to ensure level changes don't break expected outcomes.

NOTE: solutions/successes.json and solutions/failures.json should contain actual working/failing
solutions. Currently they may contain placeholder data. Solutions should be such that:
- Success cases: Actions that lead to level completion
- Failure cases: Actions that fail but don't cause immediate invalid action termination
"""

import json
import os
import pytest
from typing import List, Tuple

from interphyre.levels import load_level
from interphyre.environment import PhyreEnv
from interphyre.config import SimulationConfig


def load_solutions_file(filename: str) -> dict:
    """Load solutions from JSON file."""
    filepath = os.path.join(os.path.dirname(__file__), "solutions", filename)
    if not os.path.exists(filepath):
        return {}

    with open(filepath, "r") as f:
        content = f.read().strip()
        if not content:
            return {}
        return json.loads(content)


def run_solution_no_render(level_name: str, seed: int, action: List[float]) -> bool:
    """
    Run a solution without rendering and return success status.

    Args:
        level_name: Name of the level to test
        seed: Random seed for level generation
        action: Action to apply (list of floats)

    Returns:
        bool: True if solution succeeded, False otherwise
    """
    # Load level
    level = load_level(level_name, seed=seed)

    # Create environment without renderer (fast)
    config = SimulationConfig(fps=60, time_step=1/60, enable_profiling=False)
    env = PhyreEnv(level=level, config=config)

    # Reset and run
    env.reset()
    _, _, _, _, info = env.step(action)

    success = info.get("success", False)
    env.close()

    return success


# Load test data
SUCCESS_SOLUTIONS = load_solutions_file("successes.json")
FAILURE_SOLUTIONS = load_solutions_file("failures.json")


# ============================================================================
# Success Solution Tests
# ============================================================================


def generate_success_test_cases():
    """Generate test cases from solutions/successes.json."""
    test_cases = []
    for level_name, level_data in SUCCESS_SOLUTIONS.items():
        for seed_str, actions_list in level_data["solutions"].items():
            seed = int(seed_str)
            # actions_list is a list of actions, e.g., [[3.6, 2.8, 0.7]]
            for action in actions_list:
                test_cases.append((level_name, seed, action))
    return test_cases


def generate_failure_test_cases():
    """Generate test cases from solutions/failures.json."""
    test_cases = []
    for level_name, level_data in FAILURE_SOLUTIONS.items():
        for seed_str, actions_list in level_data["solutions"].items():
            seed = int(seed_str)
            # actions_list is a list of actions, e.g., [[1.0, 2.0, 0.5]]
            for action in actions_list:
                test_cases.append((level_name, seed, action))
    return test_cases


@pytest.mark.fast
@pytest.mark.parametrize("level_name,seed,action", generate_success_test_cases())
def test_success_solutions_succeed(level_name: str, seed: int, action: List[float]):
    """Test that solutions in solutions/successes.json achieve success."""
    success = run_solution_no_render(level_name, seed, action)
    assert success, (
        f"Expected success for {level_name} (seed {seed}) with action {action}, "
        f"but solution failed. This indicates a regression in level behavior."
    )


@pytest.mark.fast
@pytest.mark.parametrize("level_name,seed,action", generate_failure_test_cases())
def test_failure_solutions_fail(level_name: str, seed: int, action: List[float]):
    """Test that solutions in solutions/failures.json result in failure."""
    success = run_solution_no_render(level_name, seed, action)
    assert not success, (
        f"Expected failure for {level_name} (seed {seed}) with action {action}, "
        f"but solution succeeded. This indicates a regression in level behavior."
    )


# ============================================================================
# Summary Tests
# ============================================================================


@pytest.mark.fast
def test_success_file_exists_and_valid():
    """Test that solutions/successes.json exists and is valid."""
    assert SUCCESS_SOLUTIONS, "solutions/successes.json is empty or invalid"

    # Count total test cases
    total_cases = len(generate_success_test_cases())
    assert total_cases > 0, "solutions/successes.json contains no valid test cases"

    print(f"\nsolutions/successes.json: {len(SUCCESS_SOLUTIONS)} levels, {total_cases} test cases")


@pytest.mark.fast
def test_failure_file_structure():
    """Test that solutions/failures.json has correct structure (may be empty initially)."""
    # Failure file can be empty, but if present should have valid structure
    if FAILURE_SOLUTIONS:
        total_cases = len(generate_failure_test_cases())
        print(f"\nsolutions/failures.json: {len(FAILURE_SOLUTIONS)} levels, {total_cases} test cases")
    else:
        print("\nsolutions/failures.json: empty (no failure cases defined yet)")


# ============================================================================
# Optional: Smoke Test (runs a few random cases quickly)
# ============================================================================


@pytest.mark.fast
def test_solution_validation_smoke_test():
    """Quick smoke test - run a few solutions to ensure system works."""
    success_cases = generate_success_test_cases()

    if not success_cases:
        pytest.skip("No success test cases available")

    # Test first 3 success cases (or all if fewer)
    test_count = min(3, len(success_cases))

    for i in range(test_count):
        level_name, seed, action = success_cases[i]
        success = run_solution_no_render(level_name, seed, action)
        assert success, f"Smoke test failed for {level_name} (seed {seed})"

    print(f"\nSmoke test passed: {test_count}/{test_count} solutions validated")
