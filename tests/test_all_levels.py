"""
Test all levels to ensure they work correctly with the current codebase.

This test loads each level, creates an environment, and runs a basic simulation
to verify that the level can be loaded, reset, and stepped without errors.
"""

import pytest
import time
from typing import List, Dict, Any
from interphyre.levels import load_level
from interphyre.environment import PhyreEnv
from interphyre.config import SimulationConfig


def get_all_level_names() -> List[str]:
    """Get all available level names from the levels directory."""
    # These are the level names based on the files in interphyre/levels/
    level_names = [
        "basket_case",
        "catapult",
        "cliffhanger",
        "dive_bomb",
        "down_to_earth",
        "end_of_line",
        "falling_into_place",
        "flagpole_sitta",
        "just_a_nudge",
        "keyhole",
        "locust_swarm",
        "multi_red_balls",
        "off_the_rails",
        "pass_the_parcel",
        "pinball_machine",
        "pinhole",
        "seesaw",
        "staircase",
        "straight_face",
        "the_cradle",
        "the_fulcrum",
        "the_funnel",
        "tipping_point",
        "two_body_problem",
        "wedge_issue",
        "zebra_gate",
    ]
    return level_names


@pytest.mark.parametrize("level_name", get_all_level_names())
def test_level_loading_and_basic_simulation(level_name: str):
    """Test that each level can be loaded and run a basic simulation."""
    print(f"\nTesting level: {level_name}")

    # Load the level
    try:
        level = load_level(level_name, seed=42)
        print(f"  ✓ Level loaded successfully")
    except Exception as e:
        pytest.fail(f"Failed to load level {level_name}: {e}")

    # Create environment
    try:
        config = SimulationConfig(enable_profiling=False)  # Disable profiling for speed
        env = PhyreEnv(level=level, config=config)
        print(f"  ✓ Environment created successfully")
    except Exception as e:
        pytest.fail(f"Failed to create environment for {level_name}: {e}")

    # Test reset
    try:
        obs, info = env.reset()
        print(f"  ✓ Environment reset successfully")
    except Exception as e:
        pytest.fail(f"Failed to reset environment for {level_name}: {e}")

    # Test basic step with default action
    try:
        # Get a valid action (all zeros for continuous action space)
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        print(f"  ✓ Basic step completed successfully")
    except Exception as e:
        pytest.fail(f"Failed to step environment for {level_name}: {e}")

    # Test short simulation
    try:
        trace = env.simulate(steps=50, return_trace=False, verbose=False)
        print(f"  ✓ Short simulation completed successfully")
    except Exception as e:
        pytest.fail(f"Failed to simulate {level_name}: {e}")

    # Test level info
    try:
        level_info = env.get_level_info()
        assert level_info["name"] == level_name
        print(f"  ✓ Level info retrieved successfully")
    except Exception as e:
        pytest.fail(f"Failed to get level info for {level_name}: {e}")

    # Clean up
    env.close()
    print(f"  ✓ Level {level_name} completed successfully")


def test_all_levels_comprehensive():
    """Test all levels in a comprehensive manner with detailed reporting."""
    level_names = get_all_level_names()
    results = {}

    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE LEVEL TESTING")
    print(f"Testing {len(level_names)} levels...")
    print(f"{'='*60}")

    for level_name in level_names:
        print(f"\nTesting: {level_name}")
        start_time = time.perf_counter()

        try:
            # Load level
            level = load_level(level_name, seed=42)

            # Create environment
            config = SimulationConfig(enable_profiling=False)
            env = PhyreEnv(level=level, config=config)

            # Reset
            obs, info = env.reset()

            # Get level info
            level_info = env.get_level_info()

            # Run a few steps
            for step in range(10):
                action = env.action_space.sample()
                obs, reward, terminated, truncated, info = env.step(action)
                if terminated or truncated:
                    break

            # Clean up
            env.close()

            elapsed = time.perf_counter() - start_time
            results[level_name] = {
                "status": "PASS",
                "time": elapsed,
                "action_objects": level_info.get("action_objects", []),
                "total_objects": level_info.get("total_objects", 0),
            }
            print(
                f"  ✓ PASS ({elapsed:.3f}s) - {level_info.get('total_objects', 0)} objects"
            )

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            results[level_name] = {
                "status": "FAIL",
                "time": elapsed,
                "error": str(e),
            }
            print(f"  ✗ FAIL ({elapsed:.3f}s) - {e}")

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for r in results.values() if r["status"] == "PASS")
    failed = len(results) - passed
    total_time = sum(r["time"] for r in results.values())

    print(f"Total levels: {len(level_names)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total time: {total_time:.3f}s")
    print(f"Average time per level: {total_time/len(level_names):.3f}s")

    if failed > 0:
        print(f"\nFailed levels:")
        for level_name, result in results.items():
            if result["status"] == "FAIL":
                print(f"  - {level_name}: {result['error']}")

    # Assert all passed
    assert failed == 0, f"{failed} levels failed to load or run correctly"
    print(f"\n✓ All {len(level_names)} levels working correctly!")


def test_level_metadata_consistency():
    """Test that all levels have consistent metadata structure."""
    level_names = get_all_level_names()

    for level_name in level_names:
        level = load_level(level_name, seed=42)
        env = PhyreEnv(level=level)

        # Test that level has required attributes
        assert hasattr(level, "name"), f"Level {level_name} missing 'name' attribute"
        assert hasattr(
            level, "objects"
        ), f"Level {level_name} missing 'objects' attribute"
        assert hasattr(
            level, "action_objects"
        ), f"Level {level_name} missing 'action_objects' attribute"
        assert hasattr(
            level, "success_condition"
        ), f"Level {level_name} missing 'success_condition' attribute"
        assert hasattr(
            level, "metadata"
        ), f"Level {level_name} missing 'metadata' attribute"

        # Test that action_objects exist in objects
        for action_obj in level.action_objects:
            assert (
                action_obj in level.objects
            ), f"Action object '{action_obj}' not found in level objects for {level_name}"

        # Test that success_condition is callable
        assert callable(
            level.success_condition
        ), f"Success condition for {level_name} is not callable"

        env.close()


if __name__ == "__main__":
    # Run the comprehensive test
    test_all_levels_comprehensive()
 