import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import argparse
import json
import numpy as np
from interphyre.levels import load_level
from interphyre.environment import PhyreEnv
from interphyre.config import SimulationConfig
from interphyre.objects import Basket
import random
import subprocess


# --- Utility to enumerate all level names ---
def get_all_level_names():
    levels_dir = os.path.join(os.path.dirname(__file__), "../../interphyre/levels")
    level_files = [
        f
        for f in os.listdir(levels_dir)
        if f.endswith(".py") and not f.startswith("__")
    ]
    level_names = [os.path.splitext(f)[0] for f in level_files]
    return sorted(level_names)


# --- Level-specific solution finders ---
def find_basket_case_solution(level, seed, verbose=False):
    """Specialized solution finder for basket_case."""
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

    # Grid search parameters
    x_offsets = np.linspace(-0.5, 0.5, 11)
    y_offsets = np.linspace(0.0, 0.5, 6)
    sizes = [0.8, 1.0, 1.2, 1.5, 1.8, 2.0]

    found = False
    solution_action = None

    for size in sizes:
        for dx in x_offsets:
            for dy in y_offsets:
                red_ball_action = (basket_rim_x + dx, basket_rim_y + dy, size)
                action = [red_ball_action]

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
        if found:
            break

    env.close()
    return solution_action


def find_generic_solution(level, seed, verbose=False):
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

    for size in sizes:
        for dx in x_offsets:
            for dy in y_offsets:
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
        if found:
            break

    env.close()
    return solution_action


def find_catapult_solution(level, seed, verbose=False):
    """Specialized solution finder for catapult."""
    config = SimulationConfig(fps=60, time_step=1 / 60)
    env = PhyreEnv(level=level, config=config)
    obs, info = env.reset()

    # Find the gray bar (longest static bar)
    gray_bar = None
    for obj in level.objects.values():
        if hasattr(obj, "color") and obj.color == "gray" and hasattr(obj, "length"):
            if gray_bar is None or obj.length > gray_bar.length:
                gray_bar = obj
    assert gray_bar is not None, "No gray bar found in catapult!"

    # Right end of the gray bar
    bar_x = gray_bar.x + 0.5 * gray_bar.length * np.cos(gray_bar.angle)
    bar_y = gray_bar.y + 0.5 * gray_bar.length * np.sin(gray_bar.angle)

    y_offsets = np.arange(0.0, 1.01, 0.05)  # 0.0 to 1.0, step 0.05
    sizes = np.arange(1.0, 1.81, 0.1)  # 1.0 to 1.8, step 0.1

    found = False
    solution_action = None
    for size in sizes:
        for y_offset in y_offsets:
            action = [(bar_x, bar_y + y_offset, size)]
            obs, info = env.reset()
            obs, reward, done, truncated, info = env.step(action)
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
    env.close()
    return solution_action


def find_cliffhanger_solution(level, seed, verbose=False):
    """Specialized solution finder for cliffhanger."""
    config = SimulationConfig(fps=60, time_step=1 / 60)
    env = PhyreEnv(level=level, config=config)
    obs, info = env.reset()

    # Find the green bar (vertical, color 'green')
    green_bar = None
    for obj in level.objects.values():
        if hasattr(obj, "color") and obj.color == "green" and hasattr(obj, "length"):
            green_bar = obj
            break
    assert green_bar is not None, "No green bar found in cliffhanger!"

    # Top of the green bar
    bar_x = green_bar.x
    bar_y = green_bar.y + 0.5 * green_bar.length

    x_offsets = np.arange(-0.3, 0.31, 0.03)  # -0.3 to 0.3, step 0.03
    y_offsets = np.arange(0.05, 0.61, 0.05)  # 0.05 to 0.6, step 0.05
    sizes = np.arange(0.4, 1.41, 0.1)  # 0.4 to 1.4, step 0.1

    found = False
    solution_action = None
    for size in sizes:
        for x_offset in x_offsets:
            for y_offset in y_offsets:
                action = [(bar_x + x_offset, bar_y + y_offset, size)]
                obs, info = env.reset()
                obs, reward, done, truncated, info = env.step(action)
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
        if found:
            break
    env.close()
    return solution_action


def find_dive_bomb_solution(level, seed, verbose=False):
    """Specialized solution finder for dive_bomb."""
    config = SimulationConfig(fps=60, time_step=1 / 60)
    env = PhyreEnv(level=level, config=config)
    obs, info = env.reset()

    # Find the cannon top and top extension bars
    cannon_top = level.objects.get("cannon_top")
    cannon_top_extension = level.objects.get("cannon_top_extension")

    assert cannon_top is not None, "No cannon_top found in dive_bomb!"
    assert (
        cannon_top_extension is not None
    ), "No cannon_top_extension found in dive_bomb!"

    # Strategy: Drop the red ball into the gap between cannon top and top extension
    # The gap is the space between these two bars where the green ball would pass through

    # Calculate the gap position - somewhere between the two bars
    gap_x = (cannon_top.x + cannon_top_extension.x) / 2
    gap_y = (cannon_top.y + cannon_top_extension.y) / 2

    # Search in the gap area with fine-grained offsets
    y_offsets = np.arange(
        0.0, 1.51, 0.05
    )  # 0.0 to 1.5, step 0.05 (only positive y offsets)
    sizes = list(
        np.arange(0.2, 0.36, 0.01)
    )  # 0.2 to 0.35, step 0.01 (small balls for narrow gap)
    # No shuffle, try smallest first

    found = False
    solution_action = None
    attempt = 0

    for size in sizes:
        for dy in y_offsets:
            attempt += 1
            if verbose and attempt % 100 == 0:
                print(
                    f"Tried {attempt} actions so far (x={gap_x:.2f}, y={gap_y+dy:.2f}, size={size:.2f})"
                )
            action = [(gap_x, gap_y + dy, size)]
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
                    if verbose:
                        print(
                            f"Found solution: {action} in gap at ({gap_x}, {gap_y + dy}) with size {size}"
                        )
                    break
            if found:
                break
        if found:
            break

    env.close()
    return solution_action


# --- Main solution finder that routes to level-specific methods ---
def find_solution(level_name, seed, verbose=False):
    level = load_level(level_name, seed=seed)

    # Route to level-specific solution finders
    if level_name == "basket_case":
        return find_basket_case_solution(level, seed, verbose)
    elif level_name == "catapult":
        return find_catapult_solution(level, seed, verbose)
    elif level_name == "cliffhanger":
        return find_cliffhanger_solution(level, seed, verbose)
    elif level_name == "dive_bomb":
        return find_dive_bomb_solution(level, seed, verbose)
    else:
        return find_generic_solution(level, seed, verbose)


def random_search_dive_bomb_seed123(max_trials=100000):
    level_name = "dive_bomb"
    seed = 123
    config = SimulationConfig(fps=60, time_step=1 / 60)
    from interphyre.levels import load_level
    from interphyre.environment import PhyreEnv
    import json
    import subprocess

    x_min, x_max = -4.5, 4.5
    y_min, y_max = -2.0, 4.0
    size_min, size_max = 0.2, 1.0

    found_solution = False
    for trial in range(max_trials):
        x = random.uniform(x_min, x_max)
        y = random.uniform(y_min, y_max)
        size = random.uniform(size_min, size_max)
        action = [(x, y, size)]
        level = load_level(level_name, seed=seed)
        env = PhyreEnv(level=level, config=config)
        obs, info = env.reset()
        obs, reward, terminated, truncated, info = env.step(action)
        success = False
        if trace and isinstance(trace[-1][4], dict):
            success = trace[-1][4].get("success", False)
        env.close()
        if success:
            print(f"SUCCESS: x={x}, y={y}, size={size}")
            # Save solution to a temporary JSON file for visualization
            solution_list = [
                {"level": level_name, "seed": seed, "solution": [x, y, size]}
            ]
            with open("temp_dive_bomb_solution.json", "w") as f:
                json.dump(solution_list, f)
            # Visualize the solution
            subprocess.run(
                [
                    "python",
                    "visualize_solutions.py",
                    "--input",
                    "temp_dive_bomb_solution.json",
                    "--pause",
                    "3",
                ]
            )
            found_solution = True
            break
        if (trial + 1) % 1000 == 0:
            print(f"Tried {trial + 1} random actions...")
    if not found_solution:
        print("No solution found in the random search.")


# --- Main CLI script ---
def main():
    parser = argparse.ArgumentParser(
        description="Generate regression solutions for all levels."
    )
    parser.add_argument("--levels", nargs="*", help="Levels to test (default: all)")
    parser.add_argument(
        "--seeds",
        nargs="*",
        type=int,
        help="Seeds to test (default: 42 123 456 789 999)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="tests/test_solutions.json",
        help="Output file",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Discover levels
    if args.levels:
        level_names = args.levels
    else:
        level_names = get_all_level_names()

    # Default seeds
    seeds = args.seeds if args.seeds else [42, 123, 456, 789, 999]

    all_solutions = {}
    for level_name in level_names:
        print(f"\nLevel: {level_name}")
        level_solutions = {}
        for seed in seeds:
            try:
                solution = find_solution(level_name, seed, verbose=args.verbose)
                if solution:
                    level_solutions[seed] = solution
                    print(f"  ✓ Seed {seed}: {solution}")
                else:
                    print(f"  ✗ Seed {seed}: No solution found")
            except Exception as e:
                print(f"  ✗ Seed {seed}: Error - {e}")
        all_solutions[level_name] = {
            "solutions": level_solutions,
            "total_seeds": len(seeds),
            "solved_seeds": len(level_solutions),
        }

    # Save to output file
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(all_solutions, f, indent=2)
    print(f"\nSaved regression solutions to {args.output}")


if __name__ == "__main__":
    random_search_dive_bomb_seed123()
    # Comment out or skip the rest of the main logic for now
    # main()
