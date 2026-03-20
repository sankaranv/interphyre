"""
Test solution validation - ensure successes succeed and failures fail.

This test file validates that:
1. Solutions in solutions/successes.json achieve success
2. Solutions in solutions/failures.json result in failure

Solutions are stored in geometry-based (scene) format. Each scene entry
contains per-object construction kwargs and an action vector, with no
reference to random seeds.

NOTE: The actions stored in successes.json are currently placeholder data
and the success parametrize tests are expected to fail until real solutions
are recorded. The format and round-trip tests are the active regression suite.
"""

import json
import os
import pytest
from typing import List

from interphyre.levels import build_level_from_scene
from interphyre.environment import InterphyreEnv
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


def run_solution_no_render(level_name: str, scene: dict, action: List[float]) -> bool:
    """
    Run a solution without rendering and return success status.

    Args:
        level_name: Name of the level to test
        scene: Geometry dict mapping object names to construction kwargs
        action: Action to apply (list of floats)

    Returns:
        bool: True if solution succeeded, False otherwise
    """
    level = build_level_from_scene(level_name, scene)
    config = SimulationConfig(fps=60, time_step=1 / 60, enable_profiling=False)
    env = InterphyreEnv.from_level(level, config=config)
    env.reset()
    _, _, _, _, info = env.step(action)
    success = info.get("success", False)
    env.close()
    return success


# Load test data
SUCCESS_SOLUTIONS = load_solutions_file("successes.json")
FAILURE_SOLUTIONS = load_solutions_file("failures.json")


pytestmark = pytest.mark.solutions

# ============================================================================
# Success Solution Tests
# ============================================================================


def generate_success_test_cases():
    """Generate test cases from solutions/successes.json."""
    test_cases = []
    for level_name, level_data in SUCCESS_SOLUTIONS.items():
        for i, entry in enumerate(level_data["scenes"]):
            action = entry["action"]
            scene = {k: v for k, v in entry.items() if k != "action"}
            test_cases.append((level_name, i, scene, action))
    return test_cases


def generate_failure_test_cases():
    """Generate test cases from solutions/failures.json.

    Only includes entries using the scene-based format (with a "scenes" key).
    Levels still using the legacy seed-based format are skipped until migrated.
    """
    test_cases = []
    for level_name, level_data in FAILURE_SOLUTIONS.items():
        if "scenes" not in level_data:
            continue  # legacy seed-based format — skip until migrated
        for i, entry in enumerate(level_data["scenes"]):
            action = entry["action"]
            scene = {k: v for k, v in entry.items() if k != "action"}
            test_cases.append((level_name, i, scene, action))
    return test_cases


@pytest.mark.parametrize("level_name,scene_idx,scene,action", generate_success_test_cases())
def test_success_solutions_succeed(
    level_name: str, scene_idx: int, scene: dict, action: List[float]
):
    """Test that solutions in solutions/successes.json achieve success."""
    success = run_solution_no_render(level_name, scene, action)
    assert success, (
        f"Expected success for {level_name} (scene {scene_idx}) with action {action}, "
        f"but solution failed. This indicates a regression in level behavior."
    )


@pytest.mark.parametrize("level_name,scene_idx,scene,action", generate_failure_test_cases())
def test_failure_solutions_fail(
    level_name: str, scene_idx: int, scene: dict, action: List[float]
):
    """Test that solutions in solutions/failures.json result in failure."""
    success = run_solution_no_render(level_name, scene, action)
    assert not success, (
        f"Expected failure for {level_name} (scene {scene_idx}) with action {action}, "
        f"but solution succeeded. This indicates a regression in level behavior."
    )


# ============================================================================
# Summary Tests
# ============================================================================


@pytest.mark.fast
def test_success_file_exists_and_valid():
    """Test that solutions/successes.json exists and is valid."""
    assert SUCCESS_SOLUTIONS, "solutions/successes.json is empty or invalid"
    total_cases = len(generate_success_test_cases())
    assert total_cases > 0, "solutions/successes.json contains no valid test cases"
    print(
        f"\nsolutions/successes.json: {len(SUCCESS_SOLUTIONS)} levels, {total_cases} test cases"
    )


@pytest.mark.fast
def test_failure_file_structure():
    """Test that solutions/failures.json has correct structure (may be empty initially)."""
    if FAILURE_SOLUTIONS:
        total_cases = len(generate_failure_test_cases())
        print(
            f"\nsolutions/failures.json: {len(FAILURE_SOLUTIONS)} levels, {total_cases} test cases"
        )
    else:
        print("\nsolutions/failures.json: empty (no failure cases defined yet)")


# ============================================================================
# Round-trip Geometry Verification
# ============================================================================


@pytest.mark.fast
def test_scene_geometry_round_trips():
    """Verify that each stored scene re-builds to bit-identical geometry.

    Loads the level from the stored scene kwargs and checks that every
    object's position and size exactly match what was stored. This is the
    primary regression guard for the geometry migration.
    """
    from interphyre.objects.ball import Ball
    from interphyre.objects.bar import Bar

    for level_name, level_data in SUCCESS_SOLUTIONS.items():
        for i, entry in enumerate(level_data["scenes"]):
            scene = {k: v for k, v in entry.items() if k != "action"}
            level = build_level_from_scene(level_name, scene)
            for obj_name, spec in scene.items():
                obj = level.objects[obj_name]
                if isinstance(obj, Ball):
                    if "x" in spec:
                        assert obj.x == spec["x"], (
                            f"{level_name} scene {i} {obj_name}.x mismatch: "
                            f"{obj.x} != {spec['x']}"
                        )
                    if "y" in spec:
                        assert obj.y == spec["y"], (
                            f"{level_name} scene {i} {obj_name}.y mismatch: "
                            f"{obj.y} != {spec['y']}"
                        )
                    if "radius" in spec:
                        assert obj.radius == spec["radius"], (
                            f"{level_name} scene {i} {obj_name}.radius mismatch: "
                            f"{obj.radius} != {spec['radius']}"
                        )
