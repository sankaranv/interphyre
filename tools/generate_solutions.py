#!/usr/bin/env python3
"""
Solution Generator for Interphyre Levels

This script generates solutions for various levels and seeds, consolidating
all the solution finding logic into one comprehensive tool.
"""

import argparse
import json
import numpy as np
import os
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple, Any
from tqdm import tqdm

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from interphyre.levels import load_level
from interphyre.environment import PhyreEnv
from interphyre.config import SimulationConfig
from interphyre.objects import Basket
from interphyre.render import MAX_Y


def calculate_simulation_timeout(config: SimulationConfig) -> int:
    """Calculate timeout in seconds based on simulation config."""
    # Calculate total simulation time: max_steps * time_step
    simulation_time = config.max_steps * config.time_step
    # Add 20% buffer for overhead
    timeout = int(simulation_time * 1.2) + 1
    return timeout


def get_all_level_names() -> List[str]:
    """Get all available level names from the levels directory."""
    levels_dir = os.path.join(os.path.dirname(__file__), "..", "interphyre", "levels")
    level_files = [
        f
        for f in os.listdir(levels_dir)
        if f.endswith(".py") and not f.startswith("__")
    ]
    level_names = [os.path.splitext(f)[0] for f in level_files]
    return sorted(level_names)


def find_basket_case_solution(
    level, seed: int, verbose: bool = False, max_trials: int = 1000
) -> Optional[List]:
    """Random search solution finder for basket_case, using demo-style simulation."""
    config = SimulationConfig(fps=60, time_step=1 / 60)
    env = PhyreEnv(level=level, config=config)
    obs, info = env.reset()

    # Find the basket object
    basket = None
    for obj in level.objects.values():
        if isinstance(obj, Basket):
            basket = obj
            break
    assert basket is not None, "No basket found in basket_case!"

    # Compute the rim position (top center of the basket)
    basket_rim_x = basket.x
    basket_rim_y = basket.y + 1.67 * basket.scale

    found = False
    solution_action = None
    trials = 0

    for _ in range(max_trials):
        # Randomly sample parameters
        size = np.random.uniform(0.5, 1.5)
        dx = np.random.uniform(-0.5, 0.5)
        dy = np.random.uniform(0.2, 1.0)
        red_ball_action = (basket_rim_x + dx, basket_rim_y + dy, size)
        action = [red_ball_action]

        obs, info = env.reset()
        obs, reward, terminated, truncated, info = env.step(action)

        # Check success from the final step result
        success = info.get("success", False)

        if success:
            found = True
            solution_action = action
            break
        trials += 1

    env.close()
    return solution_action


def find_catapult_solution(
    level,
    seed: int,
    verbose: bool = False,
    max_trials: int = 3000,
    viz_interval: Optional[int] = None,
) -> Optional[List]:
    """Random search solution finder for catapult, using demo-style simulation with tqdm progress bar."""
    config = SimulationConfig(fps=60, time_step=1 / 60)
    timeout = calculate_simulation_timeout(config)
    env = PhyreEnv(level=level, config=config)
    obs, info = env.reset()

    # Find the gray platform (the bar that the red ball should hit)
    gray_platform = None
    for obj in level.objects.values():
        if hasattr(obj, "color") and obj.color == "gray" and hasattr(obj, "length"):
            gray_platform = obj
            break
    assert gray_platform is not None, "No gray platform found in catapult!"

    # Calculate the right edge of the gray platform
    platform_x = gray_platform.x
    platform_y = gray_platform.y
    platform_length = gray_platform.length
    platform_angle = gray_platform.angle

    # Right edge of the platform
    right_edge_x = platform_x + (platform_length / 2) * np.cos(platform_angle)
    right_edge_y = platform_y + (platform_length / 2) * np.sin(platform_angle)

    found = False
    solution_action = None
    trials = 0

    pbar = tqdm(range(max_trials), desc=f"Seed {seed}", disable=not verbose)
    for trial_num in pbar:
        # Random ball size from 0.4 to 1.2
        size = np.random.uniform(0.4, 1.2)

        # X position: right edge of gray bar minus radius plus random offset
        x_offset = np.random.uniform(-0.5, 0.5)  # Range of offsets
        x = right_edge_x - size + x_offset

        # Y position: above the gray bar with generous range of heights
        y_offset = np.random.uniform(1.0, 4.0)  # Generous height range
        y = platform_y + y_offset

        action = [(x, y, size)]

        obs, info = env.reset()
        obs, reward, terminated, truncated, info = env.step(action)

        # Check success from the final step result
        success = info.get("success", False)

        if success:
            found = True
            # Round solution to 4 decimal places
            solution_action = [[round(x, 4), round(y, 4), round(size, 4)]]
            pbar.close()
            print(f"\n🎉 SOLUTION FOUND after {trials + 1} trials!")
            print(f"Solution: {solution_action}")
            break

        trials += 1

        # Show visualization every viz_interval trials
        if viz_interval and trials % viz_interval == 0:
            print(f"\n📊 Trial {trials}: Showing current attempt...")
            print(f"   Action: x={x:.3f}, y={y:.3f}, size={size:.3f}")
            print(f"   Success: {success}")

            # Create a temporary solutions file with this attempt
            temp_solution = {"catapult": {"solutions": {str(seed): action}}}

            temp_file = f"temp_solution_{seed}_{trials}.json"
            with open(temp_file, "w") as f:
                json.dump(temp_solution, f, indent=2)

            try:
                # Run the demo script to visualize this attempt
                print(f"   🎬 Running demo visualization...")
                result = subprocess.run(
                    [
                        "python",
                        "tools/demo.py",
                        "--mode",
                        "single",
                        "--level",
                        "catapult",
                        "--seed",
                        str(seed),
                        "--solutions",
                        temp_file,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )

                if result.returncode == 0:
                    print(f"   ✅ Demo completed successfully")
                    if "Success: True" in result.stdout:
                        print(f"   🎉 This attempt was actually successful!")
                    else:
                        print(f"   ❌ This attempt failed")
                else:
                    print(f"   ⚠️ Demo had issues: {result.stderr[:100]}...")

            except subprocess.TimeoutExpired:
                print(f"   ⏰ Demo timed out")
            except Exception as e:
                print(f"   ❌ Demo error: {e}")
            finally:
                # Clean up temporary file
                try:
                    os.remove(temp_file)
                except:
                    pass

            # Pause briefly to let user see the output
            time.sleep(1)

    env.close()
    return solution_action


def find_cliffhanger_solution(
    level,
    seed: int,
    verbose: bool = False,
    max_trials: int = 1000,
    viz_interval: Optional[int] = None,
) -> Optional[List]:
    """Random search solution finder for cliffhanger, using demo-style simulation with tqdm progress bar."""
    config = SimulationConfig(fps=60, time_step=1 / 60)
    timeout = calculate_simulation_timeout(config)
    env = PhyreEnv(level=level, config=config)
    obs, info = env.reset()

    # Find the green bar and ceiling directly by their keys
    green_bar = level.objects.get("green_bar")
    ceiling = level.objects.get("ceiling")

    assert green_bar is not None, "No green bar found in cliffhanger!"
    assert ceiling is not None, "No ceiling found in cliffhanger!"

    # Top of the green bar
    bar_x = green_bar.x
    bar_y = green_bar.y + 0.5 * green_bar.length

    # Ball size range: 0.2 to 0.8 (not too big, not too small)
    min_ball_radius = 0.2
    max_ball_radius = 0.8

    found = False
    solution_action = None
    trials = 0

    pbar = tqdm(range(max_trials), desc=f"Seed {seed}", disable=not verbose)
    for trial_num in pbar:
        # Much wider ball size range
        size = np.random.uniform(min_ball_radius, max_ball_radius)

        # Y position: above the green bar but below the ceiling
        ceiling_y = ceiling.y
        max_y = ceiling_y - 0.5  # Leave some space below ceiling
        min_y = bar_y + 0.5  # At least 0.5 above the green bar
        y = np.random.uniform(min_y, max_y)

        # X position: on the same side as the green bar to tip it over
        # If green bar is on the right side of platform, place ball to the right
        # If green bar is on the left side of platform, place ball to the left
        black_platform = level.objects.get("black_platform")
        platform_center_x = black_platform.x

        if bar_x > platform_center_x:
            # Green bar is on the right side, place ball to the LEFT to tip it rightward
            x = np.random.uniform(max(-4.5, bar_x - 0.8), bar_x - 0.2)
        else:
            # Green bar is on the left side, place ball to the RIGHT to tip it leftward
            x = np.random.uniform(bar_x + 0.2, min(4.5, bar_x + 0.8))

        # Round action to 4 decimal places before testing
        action = [(round(x, 4), round(y, 4), round(size, 4))]

        obs, info = env.reset()
        obs, reward, terminated, truncated, info = env.step(action)

        # Check success from the final step result
        success = info.get("success", False)

        if success:
            found = True
            solution_action = action
            pbar.close()
            print(f"\n🎉 SOLUTION FOUND after {trials + 1} trials!")
            print(f"Solution: {solution_action}")
            break

        trials += 1

        # Show visualization every viz_interval trials
        if viz_interval and trials % viz_interval == 0:
            print(f"\n📊 Trial {trials}: Showing current attempt...")
            print(f"   Action: x={x:.3f}, y={y:.3f}, size={size:.3f}")
            print(f"   Success: {success}")

            # Create a temporary solutions file with this attempt
            temp_solution = {"cliffhanger": {"solutions": {str(seed): action}}}

            temp_file = f"temp_solution_{seed}_{trials}.json"
            with open(temp_file, "w") as f:
                json.dump(temp_solution, f, indent=2)

            try:
                # Run the demo script to visualize this attempt
                print(f"   🎬 Running demo visualization...")
                result = subprocess.run(
                    [
                        "python",
                        "tools/demo.py",
                        "--mode",
                        "single",
                        "--level",
                        "cliffhanger",
                        "--seed",
                        str(seed),
                        "--solutions",
                        temp_file,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )

                if result.returncode == 0:
                    print(f"   ✅ Demo completed successfully")
                    if "Success: True" in result.stdout:
                        print(f"   🎉 This attempt was actually successful!")
                    else:
                        print(f"   ❌ This attempt failed")
                else:
                    print(f"   ⚠️ Demo had issues: {result.stderr[:100]}...")

            except subprocess.TimeoutExpired:
                print(f"   ⏰ Demo timed out")
            except Exception as e:
                print(f"   ❌ Demo error: {e}")
            finally:
                # Clean up temporary file
                try:
                    os.remove(temp_file)
                except:
                    pass

            # Pause briefly to let user see the output
            time.sleep(1)

    env.close()
    return solution_action


def find_dive_bomb_solution(
    level,
    seed: int,
    verbose: bool = False,
    max_trials: int = 1000,
    viz_interval: Optional[int] = None,
) -> Optional[List]:
    """Random search solution finder for dive_bomb, using demo-style simulation with tqdm progress bar."""
    config = SimulationConfig(fps=60, time_step=1 / 60)
    timeout = calculate_simulation_timeout(config)
    env = PhyreEnv(level=level, config=config)
    obs, info = env.reset()

    # Find the cannon top and top extension to calculate the gap midpoint
    cannon_top = level.objects.get("cannon_top")
    cannon_top_extension = level.objects.get("cannon_top_extension")

    assert cannon_top is not None, "No cannon_top found in dive_bomb!"
    assert (
        cannon_top_extension is not None
    ), "No cannon_top_extension found in dive_bomb!"

    # Calculate the right end of the cannon top (where the gap starts)
    cannon_top_angle_rad = np.radians(cannon_top.angle)
    cannon_top_right_x = cannon_top.x + (cannon_top.length / 2) * np.cos(
        cannon_top_angle_rad
    )
    cannon_top_right_y = cannon_top.y + (cannon_top.length / 2) * np.sin(
        cannon_top_angle_rad
    )

    # Calculate the left end of the cannon top extension (where the gap ends)
    extension_angle_rad = np.radians(cannon_top_extension.angle)
    extension_left_x = cannon_top_extension.x - (
        cannon_top_extension.length / 2
    ) * np.cos(extension_angle_rad)
    extension_left_y = cannon_top_extension.y - (
        cannon_top_extension.length / 2
    ) * np.sin(extension_angle_rad)

    # Calculate the midpoint of the gap
    gap_midpoint_x = (cannon_top_right_x + extension_left_x) / 2
    gap_midpoint_y = (cannon_top_right_y + extension_left_y) / 2

    found = False
    solution_action = None
    trials = 0

    pbar = tqdm(range(max_trials), desc=f"Seed {seed}", disable=not verbose)
    for trial_num in pbar:
        # Ball size range 0.05 to 0.25 (very small to fit through the gap)
        size = np.random.uniform(0.05, 0.25)

        # Much more precise X positioning around the gap
        x_offset = np.random.uniform(-0.3, 0.3)  # Tighter offset around the gap
        x = gap_midpoint_x + x_offset

        # Y position: much closer to the gap, including negative offsets
        y_offset = np.random.uniform(-0.5, 1.0)  # Closer range, including below the gap
        y = gap_midpoint_y + y_offset

        action = [(x, y, size)]

        obs, info = env.reset()
        obs, reward, terminated, truncated, info = env.step(action)

        # Check success from the final step result
        success = info.get("success", False)

        if success:
            found = True
            # Round solution to 4 decimal places
            solution_action = [[round(x, 4), round(y, 4), round(size, 4)]]
            pbar.close()
            print(f"\n🎉 SOLUTION FOUND after {trials + 1} trials!")
            print(f"Solution: {solution_action}")
            break

        trials += 1

        # Show visualization every viz_interval trials
        if viz_interval and trials % viz_interval == 0:
            print(f"\n📊 Trial {trials}: Showing current attempt...")
            print(f"   Action: x={x:.3f}, y={y:.3f}, size={size:.3f}")
            print(f"   Success: {success}")
            print(f"   Gap midpoint: x={gap_midpoint_x:.3f}, y={gap_midpoint_y:.3f}")
            print(
                f"   Gap dimensions: cannon_top_right=({cannon_top_right_x:.3f}, {cannon_top_right_y:.3f})"
            )
            print(
                f"   Gap dimensions: extension_left=({extension_left_x:.3f}, {extension_left_y:.3f})"
            )
            print(
                f"   Strategy: Dropping small ball precisely through gap between cannon top and extension"
            )

            # Create a temporary solutions file with this attempt
            temp_solution = {"dive_bomb": {"solutions": {str(seed): action}}}

            temp_file = f"temp_solution_{seed}_{trials}.json"
            with open(temp_file, "w") as f:
                json.dump(temp_solution, f, indent=2)

            try:
                # Run the demo script to visualize this attempt
                print(f"   🎬 Running demo visualization...")
                result = subprocess.run(
                    [
                        "python",
                        "tools/demo.py",
                        "--mode",
                        "single",
                        "--level",
                        "dive_bomb",
                        "--seed",
                        str(seed),
                        "--solutions",
                        temp_file,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )

                if result.returncode == 0:
                    print(f"   ✅ Demo completed successfully")
                    if "Success: True" in result.stdout:
                        print(f"   🎉 This attempt was actually successful!")
                    else:
                        print(f"   ❌ Demo confirmed failure")
                else:
                    print(f"   ⏰ Demo timed out")
            except subprocess.TimeoutExpired:
                print(f"   ⏰ Demo timed out")
            except Exception as e:
                print(f"   ❌ Demo error: {e}")
            finally:
                # Clean up temporary file
                try:
                    os.remove(temp_file)
                except:
                    pass

    env.close()
    return solution_action


def find_generic_solution(
    level, seed: int, verbose: bool = False, max_trials: int = 1000
) -> Optional[List]:
    """Generic solution finder for most levels."""
    config = SimulationConfig(fps=60, time_step=1 / 60)
    env = PhyreEnv(level=level, config=config)
    obs, info = env.reset()

    action_objects = getattr(level, "action_objects", [])
    if not action_objects:
        env.close()
        return None

    # Generic grid search parameters
    x_offsets = np.linspace(-2.0, 2.0, 21)
    y_offsets = np.linspace(-2.0, 2.0, 21)
    sizes = [0.5, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0]

    found = False
    solution_action = None
    trials = 0

    for size in sizes:
        for dx in x_offsets:
            for dy in y_offsets:
                if trials >= max_trials:
                    break
                trials += 1

                # Position relative to action object
                obj_name = action_objects[0]
                obj = level.objects[obj_name]
                action = [(obj.x + dx, obj.y + dy, size)]

                obs, info = env.reset()
                obs, reward, done, truncated, info = env.step(action)

                # Run simulation step by step until success
                for step in range(500):
                    env.engine.world.Step(
                        config.time_step, config.velocity_iters, config.position_iters
                    )
                    env.engine.time_update(config.time_step)
                    if env.level.success_condition(env.engine):
                        found = True
                        solution_action = action
                        break

                if found:
                    break
            if found:
                break
        if found or trials >= max_trials:
            break

    env.close()
    return solution_action


def find_down_to_earth_solution(
    level,
    seed: int,
    verbose: bool = False,
    max_trials: int = 1000,
    viz_interval: Optional[int] = None,
) -> Optional[List]:
    """Strategic solution finder for down_to_earth using gap analysis and ball placement."""
    config = SimulationConfig(fps=60, time_step=1 / 60)
    env = PhyreEnv(level=level, config=config)
    obs, info = env.reset()

    # Get level objects
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    high_platform = level.objects["high_platform"]

    # Platform analysis
    platform_x = high_platform.x
    platform_length = high_platform.length
    platform_left = platform_x - platform_length / 2
    platform_right = platform_x + platform_length / 2

    # Green ball position
    green_x = green_ball.x
    green_y = green_ball.y
    green_radius = green_ball.radius

    # Calculate gaps to left and right
    left_gap = platform_left - (-5.0)  # Distance to left wall
    right_gap = 5.0 - platform_right  # Distance to right wall

    # Determine which side has more feasible gap
    # Consider both gap size and distance from green ball
    left_distance = abs(green_x - platform_left)
    right_distance = abs(green_x - platform_right)

    # Weighted decision: prefer larger gap, but also consider distance
    left_score = left_gap - left_distance * 0.5
    right_score = right_gap - right_distance * 0.5

    found = False
    solution_action = None
    trials = 0

    pbar = tqdm(range(max_trials), desc=f"Seed {seed}", disable=not verbose)
    for trial_num in pbar:
        # Choose side with better score
        if left_score > right_score:
            target_side = "left"
        else:
            target_side = "right"

        # Calculate red ball position with some randomization
        # Y position: above green ball with some clearance and variation
        base_y = green_y + green_radius + red_ball.radius + 0.1
        y_offset = np.random.uniform(-0.1, 0.2)  # Small variation in height
        red_y = base_y + y_offset

        # X position: offset to push green ball toward target side with variation
        if target_side == "left":
            # Push left: place red ball to the right of green ball
            base_x = green_x + green_radius * 0.8
            x_offset = np.random.uniform(-0.3, 0.3)  # Variation in offset
            red_x = base_x + x_offset
        else:
            # Push right: place red ball to the left of green ball
            base_x = green_x - green_radius * 0.8
            x_offset = np.random.uniform(-0.3, 0.3)  # Variation in offset
            red_x = base_x + x_offset

        # Ball size variation
        size = np.random.uniform(red_ball.radius * 0.8, red_ball.radius * 1.2)

        # Ensure red ball stays within bounds
        red_x = np.clip(red_x, -4.5, 4.5)
        red_y = np.clip(red_y, -2, 4)

        action = [(red_x, red_y, size)]

        obs, info = env.reset()
        obs, reward, done, truncated, info = env.step(action)
        trace = env.simulate(steps=500, return_trace=True)

        # Check success using the level's success condition
        success = False
        if trace:
            success = level.success_condition(env.engine)

        if success:
            found = True
            # Round solution to 4 decimal places
            solution_action = [[round(red_x, 4), round(red_y, 4), round(size, 4)]]
            pbar.close()
            print(f"\n🎉 SOLUTION FOUND after {trials + 1} trials!")
            print(f"Solution: {solution_action}")
            break

        trials += 1

        # Show visualization every viz_interval trials
        if viz_interval and trials % viz_interval == 0:
            print(f"\n📊 Trial {trials}: Showing current attempt...")
            print(f"   Action: x={red_x:.3f}, y={red_y:.3f}, size={size:.3f}")
            print(f"   Success: {success}")
            print(f"   Platform: x={platform_x:.3f}, length={platform_length:.3f}")
            print(
                f"   Green ball: x={green_x:.3f}, y={green_y:.3f}, radius={green_radius:.3f}"
            )
            print(f"   Left gap: {left_gap:.3f}, right gap: {right_gap:.3f}")
            print(f"   Left score: {left_score:.3f}, right score: {right_score:.3f}")
            print(f"   Strategy: Pushing green ball toward {target_side} side")

            # Create a temporary solutions file with this attempt
            temp_solution = {"down_to_earth": {"solutions": {str(seed): action}}}

            temp_file = f"temp_solution_{seed}_{trials}.json"
            with open(temp_file, "w") as f:
                json.dump(temp_solution, f, indent=2)

            try:
                # Run the demo script to visualize this attempt
                print(f"   🎬 Running demo visualization...")
                result = subprocess.run(
                    [
                        "python",
                        "tools/demo.py",
                        "--mode",
                        "single",
                        "--level",
                        "down_to_earth",
                        "--seed",
                        str(seed),
                        "--solutions",
                        temp_file,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    print(f"   ✅ Demo completed successfully")
                    if "Success: True" in result.stdout:
                        print(f"   🎉 This attempt was actually successful!")
                    else:
                        print(f"   ❌ Demo confirmed failure")
                else:
                    print(f"   ⚠️ Demo had issues: {result.stderr[:100]}...")

            except subprocess.TimeoutExpired:
                print(f"   ⏰ Demo timed out")
            except Exception as e:
                print(f"   ❌ Demo error: {e}")
            finally:
                # Clean up temporary file
                try:
                    os.remove(temp_file)
                except:
                    pass

            # Pause briefly to let user see the output
            time.sleep(1)

    env.close()
    return solution_action


def find_end_of_line_solution(
    level,
    seed: int,
    verbose: bool = False,
    max_trials: int = 1000,
    viz_interval: Optional[int] = None,
) -> Optional[List]:
    """Strategic solution finder for end_of_line using purple wall analysis and ball placement."""
    config = SimulationConfig(fps=60, time_step=1 / 60)
    timeout = calculate_simulation_timeout(config)
    env = PhyreEnv(level=level, config=config)
    obs, info = env.reset()

    # Get level objects
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    purple_wall = level.objects["purple_wall"]
    table_top = level.objects["table_top"]

    # Purple wall analysis
    purple_wall_x = purple_wall.x
    purple_wall_side = "left" if purple_wall_x < 0 else "right"

    # Green ball position
    green_x = green_ball.x
    green_y = green_ball.y
    green_radius = green_ball.radius

    # Table analysis
    table_x = table_top.x
    table_length = table_top.length
    table_left = table_x - table_length / 2
    table_right = table_x + table_length / 2

    found = False
    solution_action = None
    trials = 0

    pbar = tqdm(range(max_trials), desc=f"Seed {seed}", disable=not verbose)
    for trial_num in pbar:
        # Calculate red ball position with some randomization
        # Y position: above green ball with some clearance and variation
        base_y = green_y + green_radius + red_ball.radius + 0.1
        y_offset = np.random.uniform(-0.1, 0.2)  # Small variation in height
        red_y = base_y + y_offset

        # X position: offset to push green ball toward purple wall
        if purple_wall_side == "left":
            # Purple wall is on the left, push green ball left
            # Place red ball to the right of green ball
            base_x = green_x + green_radius * 0.8
            x_offset = np.random.uniform(-0.3, 0.3)  # Variation in offset
            red_x = base_x + x_offset
        else:
            # Purple wall is on the right, push green ball right
            # Place red ball to the left of green ball
            base_x = green_x - green_radius * 0.8
            x_offset = np.random.uniform(-0.3, 0.3)  # Variation in offset
            red_x = base_x + x_offset

        # Ball size variation - make it roughly the size of green ball or bigger
        size = np.random.uniform(green_radius * 0.8, green_radius * 1.5)

        # Ensure red ball stays within bounds
        red_x = np.clip(red_x, -4.5, 4.5)
        red_y = np.clip(red_y, -2, 4)

        action = [(red_x, red_y, size)]

        obs, info = env.reset()
        obs, reward, done, truncated, info = env.step(action)
        trace = env.simulate(steps=500, return_trace=True)

        # Check success using the level's success condition
        success = False
        if trace:
            success = level.success_condition(env.engine)

        if success:
            found = True
            # Round solution to 4 decimal places
            solution_action = [[round(red_x, 4), round(red_y, 4), round(size, 4)]]
            pbar.close()
            print(f"\n🎉 SOLUTION FOUND after {trials + 1} trials!")
            print(f"Solution: {solution_action}")
            break

        trials += 1

        # Show visualization every viz_interval trials
        if viz_interval and trials % viz_interval == 0:
            print(f"\n📊 Trial {trials}: Showing current attempt...")
            print(f"   Action: x={red_x:.3f}, y={red_y:.3f}, size={size:.3f}")
            print(f"   Success: {success}")
            print(f"   Purple wall: x={purple_wall_x:.3f} ({purple_wall_side} side)")
            print(f"   Table: x={table_x:.3f}, length={table_length:.3f}")
            print(
                f"   Green ball: x={green_x:.3f}, y={green_y:.3f}, radius={green_radius:.3f}"
            )
            print(
                f"   Strategy: Pushing green ball toward {purple_wall_side} side (purple wall)"
            )

            # Create a temporary solutions file with this attempt
            temp_solution = {"end_of_line": {"solutions": {str(seed): action}}}

            temp_file = f"temp_solution_{seed}_{trials}.json"
            with open(temp_file, "w") as f:
                json.dump(temp_solution, f, indent=2)

            try:
                # Run the demo script to visualize this attempt
                print(f"   🎬 Running demo visualization...")
                result = subprocess.run(
                    [
                        "python",
                        "tools/demo.py",
                        "--mode",
                        "single",
                        "--level",
                        "end_of_line",
                        "--seed",
                        str(seed),
                        "--solutions",
                        temp_file,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )

                if result.returncode == 0:
                    print(f"   ✅ Demo completed successfully")
                    if "Success: True" in result.stdout:
                        print(f"   🎉 This attempt was actually successful!")
                    else:
                        print(f"   ❌ Demo confirmed failure")
                else:
                    print(f"   ⚠️ Demo had issues: {result.stderr[:100]}...")

            except subprocess.TimeoutExpired:
                print(f"   ⏰ Demo timed out")
            except Exception as e:
                print(f"   ❌ Demo error: {e}")
            finally:
                # Clean up temporary file
                try:
                    os.remove(temp_file)
                except:
                    pass

            # Pause briefly to let user see the output
            time.sleep(1)

    env.close()
    return solution_action


def find_falling_into_place_solution(
    level,
    seed: int,
    verbose: bool = False,
    max_trials: int = 1000,
    viz_interval: Optional[int] = None,
) -> Optional[List]:
    """Strategic solution finder for falling_into_place using gap-targeting strategy."""
    config = SimulationConfig(fps=60, time_step=1 / 60)
    timeout = calculate_simulation_timeout(config)
    env = PhyreEnv(level=level, config=config)
    obs, info = env.reset()

    # Get level objects
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    left_bar = level.objects["left_bar"]
    right_bar = level.objects["right_bar"]
    blue_jar = level.objects["blue_jar"]

    # Analyze green ball position relative to bars
    green_x = green_ball.x
    green_y = green_ball.y
    green_radius = green_ball.radius

    # Determine which side the green ball is on
    green_ball_side = "left" if green_x < 0 else "right"

    # Calculate the center gap (between the bars)
    left_bar_x = left_bar.x
    right_bar_x = right_bar.x
    center_gap_x = (left_bar_x + right_bar_x) / 2  # Should be around 0

    # Blue jar position
    jar_x = blue_jar.x
    jar_y = blue_jar.y

    found = False
    solution_action = None
    trials = 0

    pbar = tqdm(range(max_trials), desc=f"Seed {seed}", disable=not verbose)
    for trial_num in pbar:
        # Strategy: Place red ball to knock green ball toward the center gap
        # Similar to end_of_line strategy but targeting the gap between bars

        # Calculate red ball position with strategic offset
        if green_ball_side == "left":
            # Green ball is on left bar, push it right toward center
            # Position red ball to the left of green ball to push it right
            base_offset = np.random.uniform(0.8, 0.95)  # Close to green ball radius
            base_x = green_x - green_radius * base_offset
            x_offset = np.random.uniform(-0.1, 0.1)  # Small variation for fine-tuning
            red_x = base_x + x_offset
        else:
            # Green ball is on right bar, push it left toward center
            # Position red ball to the right of green ball to push it left
            base_offset = np.random.uniform(0.8, 0.95)  # Close to green ball radius
            base_x = green_x + green_radius * base_offset
            x_offset = np.random.uniform(-0.1, 0.1)  # Small variation for fine-tuning
            red_x = base_x + x_offset

        # Ball size: larger than green ball for more forceful impact
        size = np.random.uniform(green_radius * 1.2, green_radius * 1.8)

        # Y position: at maximum height for maximum momentum
        red_y = MAX_Y - size  # MAX_Y - red ball radius

        # Ensure red ball stays within bounds
        red_x = np.clip(red_x, -4.5, 4.5)
        red_y = np.clip(red_y, -2, 4)

        action = [(red_x, red_y, size)]

        obs, info = env.reset()
        obs, reward, done, truncated, info = env.step(action)
        trace = env.simulate(steps=500, return_trace=True)

        # Check success using the level's success condition
        success = False
        if trace:
            success = level.success_condition(env.engine)

        if success:
            found = True
            # Round solution to 4 decimal places
            solution_action = [[round(red_x, 4), round(red_y, 4), round(size, 4)]]
            pbar.close()
            print(f"\n🎉 SOLUTION FOUND after {trials + 1} trials!")
            print(f"Solution: {solution_action}")
            break

        trials += 1

        # Show visualization every viz_interval trials
        if viz_interval and trials % viz_interval == 0:
            print(f"\n📊 Trial {trials}: Showing current attempt...")
            print(f"   Action: x={red_x:.3f}, y={red_y:.3f}, size={size:.3f}")
            print(f"   Success: {success}")
            print(
                f"   Contact duration: {env.engine.get_contact_duration('green_ball', 'blue_jar'):.2f}s (need 3.0s)"
            )
            print(
                f"   Green ball: x={green_x:.3f}, y={green_y:.3f}, side={green_ball_side}"
            )
            print(f"   Center gap: x={center_gap_x:.3f}")
            print(f"   Blue jar: x={jar_x:.3f}, y={jar_y:.3f}")
            print(f"   Strategy: Pushing green ball toward center gap")

            # Create a temporary solutions file with this attempt
            temp_solution = {"falling_into_place": {"solutions": {str(seed): action}}}

            temp_file = f"temp_solution_{seed}_{trials}.json"
            with open(temp_file, "w") as f:
                json.dump(temp_solution, f, indent=2)

            try:
                # Run the demo script to visualize this attempt
                print(f"   🎬 Running demo visualization...")
                result = subprocess.run(
                    [
                        "python",
                        "tools/demo.py",
                        "--mode",
                        "single",
                        "--level",
                        "falling_into_place",
                        "--seed",
                        str(seed),
                        "--solutions",
                        temp_file,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )

                if result.returncode == 0:
                    print(f"   ✅ Demo completed successfully")
                    if "Success: True" in result.stdout:
                        print(f"   🎉 This attempt was actually successful!")
                    else:
                        print(f"   ❌ Demo confirmed failure")
                else:
                    print(f"   ⚠️ Demo had issues: {result.stderr[:100]}...")

            except subprocess.TimeoutExpired:
                print(f"   ⏰ Demo timed out")
            except Exception as e:
                print(f"   ❌ Demo error: {e}")
            finally:
                # Clean up temporary file
                try:
                    os.remove(temp_file)
                except:
                    pass

            # Pause briefly to let user see the output
            time.sleep(1)

    env.close()
    return solution_action


def find_solution(
    level_name: str,
    seed: int,
    verbose: bool = False,
    max_trials: int = 1000,
    viz_interval: Optional[int] = None,
) -> Optional[List]:
    """Main solution finder that routes to level-specific methods."""
    level = load_level(level_name, seed=seed)

    # Route to level-specific solution finders
    if level_name == "basket_case":
        return find_basket_case_solution(level, seed, verbose, max_trials)
    elif level_name == "catapult":
        return find_catapult_solution(level, seed, verbose, max_trials, viz_interval)
    elif level_name == "cliffhanger":
        return find_cliffhanger_solution(level, seed, verbose, max_trials, viz_interval)
    elif level_name == "dive_bomb":
        return find_dive_bomb_solution(level, seed, verbose, max_trials, viz_interval)
    elif level_name == "down_to_earth":
        return find_down_to_earth_solution(
            level, seed, verbose, max_trials, viz_interval
        )
    elif level_name == "end_of_line":
        return find_end_of_line_solution(level, seed, verbose, max_trials, viz_interval)
    elif level_name == "falling_into_place":
        return find_falling_into_place_solution(
            level, seed, verbose, max_trials, viz_interval
        )
    else:
        return find_generic_solution(level, seed, verbose, max_trials)


def generate_solutions(
    levels: Optional[List[str]] = None,
    seeds: Optional[List[int]] = None,
    output_file: str = "solutions.json",
    verbose: bool = False,
    max_trials: int = 1000,
    overwrite: bool = False,
    viz_interval: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate solutions for specified levels and seeds.
    Merges with existing solutions if output_file exists.
    Outputs a clean, compact, and rounded JSON file.
    Saves after each seed for robustness.
    If overwrite is True, always regenerate solutions for the specified seeds.
    """
    import json
    import os

    # Default levels (first 5 levels)
    if levels is None:
        all_levels = get_all_level_names()
        levels = all_levels[:5]  # First 5 levels

    # Default seeds (10 seeds)
    if seeds is None:
        seeds = [42, 123, 456, 789, 999, 111, 222, 333, 444, 555]

    # Load existing solutions if file exists
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            all_solutions = json.load(f)
    else:
        all_solutions = {}

    print(
        f"Generating solutions for {len(levels)} levels with {len(seeds)} seeds each..."
    )
    print(f"Levels: {', '.join(levels)}")
    print(f"Seeds: {seeds}")
    print(f"Max trials per seed: {max_trials}")
    print("-" * 60)

    for level_name in levels:
        print(f"\nLevel: {level_name}")
        level_solutions = all_solutions.get(level_name, {}).get("solutions", {})

        for seed in seeds:
            # If overwrite is False and we already have a solution for this seed, skip it
            # If overwrite is True, we'll regenerate the solution even if it exists
            if not overwrite and str(seed) in level_solutions:
                if verbose:
                    print(f"  Skipping seed {seed} (already solved)")
                continue
            try:
                if verbose:
                    print(f"  Testing seed {seed}...")

                solution = find_solution(
                    level_name,
                    seed,
                    verbose=verbose,
                    max_trials=max_trials,
                    viz_interval=viz_interval,
                )

                if solution:
                    # Round all numbers to 4 decimal places
                    rounded_solution = [
                        [
                            round(float(x), 4) if isinstance(x, (float, int)) else x
                            for x in action
                        ]
                        for action in solution
                    ]
                    level_solutions[str(seed)] = rounded_solution
                    if verbose:
                        print(f"  ✓ Seed {seed}: {rounded_solution}")
                    else:
                        print(f"  ✓ Seed {seed}")
                else:
                    if verbose:
                        print(
                            f"  ✗ Seed {seed}: No solution found (max trials reached)"
                        )
                    else:
                        print(f"  ✗ Seed {seed}")

                # Save after each seed
                all_solutions[level_name] = {"solutions": level_solutions}
                output_dir = os.path.dirname(output_file)
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                # Custom JSON formatting with lists on single lines
                with open(output_file, "w") as f:
                    json_str = json.dumps(
                        all_solutions,
                        indent=2,
                        separators=(",", ": "),
                        ensure_ascii=False,
                    )
                    # Replace multi-line lists with single-line lists
                    import re

                    # Pattern to match lists with numbers on separate lines
                    pattern = r"\[\s*\n\s*([0-9.-]+),\s*\n\s*([0-9.-]+),\s*\n\s*([0-9.-]+)\s*\n\s*\]"
                    replacement = r"[\1, \2, \3]"
                    json_str = re.sub(pattern, replacement, json_str)
                    f.write(json_str)

            except Exception as e:
                if verbose:
                    print(f"  ✗ Seed {seed}: Error - {e}")
                else:
                    print(f"  ✗ Seed {seed}: Error")

        # Update the level's solutions in all_solutions
        all_solutions[level_name] = {"solutions": level_solutions}

        success_rate = len(level_solutions) / len(seeds) * 100
        print(
            f"  Success rate: {success_rate:.1f}% ({len(level_solutions)}/{len(seeds)})"
        )

    print(f"\nSaved solutions to {output_file}")

    # Summary
    total_solutions = sum(
        len(level_data["solutions"]) for level_data in all_solutions.values()
    )
    total_possible = sum(
        len(level_data["solutions"]) for level_data in all_solutions.values()
    )
    overall_success_rate = (
        total_solutions / total_possible * 100 if total_possible else 0
    )

    print(f"\nSUMMARY:")
    print(
        f"Total solutions found: {total_solutions}/{total_possible} ({overall_success_rate:.1f}%)"
    )

    return all_solutions


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Generate solutions for Interphyre levels"
    )
    parser.add_argument(
        "--levels", nargs="*", help="Levels to test (default: first 5 levels)"
    )
    parser.add_argument(
        "--seeds",
        nargs="*",
        type=int,
        help="Seeds to test (default: 10 seeds from 42 to 555)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="solutions.json",
        help="Output file path (default: solutions.json)",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--max-trials",
        type=int,
        default=1000,
        help="Maximum trials per seed before giving up (default: 1000)",
    )
    parser.add_argument(
        "--list-levels", action="store_true", help="List all available levels and exit"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing solutions for specified seeds",
    )
    parser.add_argument(
        "--visualize-interval",
        type=int,
        help="Show visualization every N trials (e.g., 100 for every 100th trial)",
    )

    args = parser.parse_args()

    if args.list_levels:
        levels = get_all_level_names()
        print("Available levels:")
        for i, level in enumerate(levels, 1):
            print(f"  {i:2d}. {level}")
        return

    generate_solutions(
        levels=args.levels,
        seeds=args.seeds,
        output_file=args.output,
        verbose=args.verbose,
        max_trials=args.max_trials,
        overwrite=args.overwrite,
        viz_interval=args.visualize_interval,
    )


if __name__ == "__main__":
    main()
