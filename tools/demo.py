import argparse
import json
import numpy as np
import os
import sys
from typing import Optional

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from interphyre.levels import load_level
from interphyre.environment import PhyreEnv
from interphyre.render.pygame import PygameRenderer
from interphyre.config import SimulationConfig


def visualize_solution_from_file(
    solutions_file: str, level_name: str, seed: int, pause_time: float = 2.0
):
    """Visualize a specific solution from the solutions.json file."""
    # Load solutions
    if not os.path.exists(solutions_file):
        print(f"Solutions file not found: {solutions_file}")
        return False

    with open(solutions_file, "r") as f:
        solutions_data = json.load(f)

    if level_name not in solutions_data:
        print(f"Level '{level_name}' not found in solutions file")
        return False

    level_data = solutions_data[level_name]
    seed_str = str(seed)

    if seed_str not in level_data["solutions"]:
        print(f"Seed {seed} not found for level '{level_name}'")
        return False

    action = level_data["solutions"][seed_str]
    print(f"Visualizing {level_name} (seed {seed}): {action}")

    # Create configuration
    config = SimulationConfig(fps=60, time_step=1 / 60, enable_profiling=False)

    # Create renderer
    renderer = PygameRenderer(width=600, height=600, ppm=60)

    try:
        # Load level and create environment
        level = load_level(level_name, seed=seed)
        env = PhyreEnv(level=level, renderer=renderer, config=config)

        # Reset environment
        obs, info = env.reset()

        # Apply action
        obs, reward, done, truncated, info = env.step(action)

        # Run simulation with visualization
        trace = env.simulate(steps=500, return_trace=True)

        # Check success
        success = False
        if trace and isinstance(trace[-1][4], dict):
            success = trace[-1][4].get("success", False)

        print(f"Success: {success}")

        # Pause to show the result
        renderer.wait(int(pause_time * 1000))

        return success

    except Exception as e:
        print(f"Error visualizing {level_name} (seed {seed}): {e}")
        return False
    finally:
        env.close()
        renderer.close()


def visualize_all_solutions(
    solutions_file: str,
    pause_time: float = 2.0,
    max_viz: Optional[int] = None,
    level_filter: Optional[str] = None,
):
    """Visualize all solutions from the solutions.json file."""
    # Load solutions
    if not os.path.exists(solutions_file):
        print(f"Solutions file not found: {solutions_file}")
        return

    with open(solutions_file, "r") as f:
        solutions_data = json.load(f)

    print(f"Visualizing solutions from {solutions_file}")
    print(f"Found {len(solutions_data)} levels")
    if level_filter:
        print(f"Filtering to level: {level_filter}")
    print("-" * 60)

    # Collect all visualizations
    all_visualizations = []
    for level_name, level_data in solutions_data.items():
        # Skip if level filter is specified and doesn't match
        if level_filter and level_name != level_filter:
            continue
        for seed_str, action in level_data["solutions"].items():
            all_visualizations.append((level_name, int(seed_str), action))

    # Limit visualizations if requested
    if max_viz is not None and len(all_visualizations) > max_viz:
        all_visualizations = all_visualizations[:max_viz]
        print(f"Limited to {max_viz} visualizations")

    print(f"Running {len(all_visualizations)} visualizations...")
    print()

    successful = 0
    failed = 0

    for i, (level_name, seed, action) in enumerate(all_visualizations, 1):
        print(
            f"Visualization {i}/{len(all_visualizations)}: {level_name} (seed {seed})"
        )

        success = visualize_solution_from_file(
            solutions_file, level_name, seed, pause_time
        )

        if success:
            successful += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"VISUALIZATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total visualizations: {len(all_visualizations)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    if len(all_visualizations) > 0:
        success_rate = successful / len(all_visualizations) * 100
        print(f"Success rate: {success_rate:.1f}%")


def run_random_demo(
    level_name: str,
    seed: Optional[int] = None,
    max_trials: int = 20,
    fps: int = 60,
    profile: bool = False,
):
    """Run the original demo functionality with random actions."""
    # Create configuration with performance profiling if requested
    config = SimulationConfig(
        fps=fps,
        time_step=1 / fps,
        enable_profiling=profile,
        log_step_times=profile,
    )

    # Instantiate the renderer
    renderer = PygameRenderer(width=600, height=600, ppm=60)

    trial = 0
    success = False
    while trial < max_trials:
        trial += 1
        trial_seed = np.random.randint(0, 100000) if seed is None else seed
        level = load_level(level_name, seed=trial_seed)
        env = PhyreEnv(level=level, renderer=renderer, config=config)

        # Reset the environment. This instantiates the Box2DEngine and loads level objects.
        obs, info = env.reset()

        # Provide random actions for all levels
        action_x = np.random.uniform(-4.5, 4.5)
        action_y = np.random.uniform(-2, 4)
        action_size = np.random.uniform(0.1, 2.0)  # Random size within bounds
        action = [(action_x, action_y, action_size) for _ in level.action_objects]

        # Execute a step to apply the action (which is only placed once) and advance the simulation.
        obs, reward, done, truncated, info = env.step(action)

        # Run additional simulation steps (if needed).
        trace = env.simulate(steps=500, return_trace=True)

        # Debug output: print the last step's done, reward, and info
        if trace and len(trace) > 0:
            last_obs, last_reward, last_done, last_truncated, last_info = trace[-1]
            print(
                f"[DEBUG] Last step: done={last_done}, reward={last_reward}, info={last_info}"
            )

            if last_done:
                print(f"Success!")

                # Print performance stats if profiling was enabled
                if profile:
                    stats = env.get_performance_stats()
                    print("\nPerformance Statistics:")
                    for metric, data in stats.items():
                        print(f"  {metric}:")
                        for key, value in data.items():
                            print(
                                f"    {key}: {value:.6f}s"
                                if isinstance(value, float)
                                else f"    {key}: {value}"
                            )

                    # Print contact statistics
                    contact_stats = env.get_contact_statistics()
                    if contact_stats:
                        print("\nContact Statistics:")
                        for key, value in contact_stats.items():
                            if key != "pair_counts":
                                print(f"  {key}: {value}")
                        if "pair_counts" in contact_stats:
                            print("  Contact pairs:")
                            for pair, counts in contact_stats["pair_counts"].items():
                                print(f"    {pair}: {counts}")
                success = True
                break
    if not success:
        print(f"No success after {max_trials} trials.")

    # Render the final state to the screen for a short period before closing.
    renderer.wait(500)
    env.close()


def main():
    parser = argparse.ArgumentParser(description="Interphyre Demo Script")

    # Mode selection
    parser.add_argument(
        "--mode",
        type=str,
        choices=["random", "solutions", "single"],
        default="random",
        help="Demo mode: random (original), solutions (from file), or single (one solution)",
    )

    # Solutions file mode
    parser.add_argument(
        "--solutions",
        type=str,
        default="tools/solutions.json",
        help="Path to solutions JSON file (for solutions mode)",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=2.0,
        help="Seconds to pause between visualizations (for solutions mode)",
    )
    parser.add_argument(
        "--max-viz",
        type=int,
        help="Maximum number of visualizations to run (for solutions mode)",
    )

    # Single solution mode
    parser.add_argument(
        "--level",
        type=str,
        help="Level name (for single solution mode or to filter solutions mode)",
    )
    parser.add_argument(
        "--seed", type=int, help="Seed (for single solution mode or random mode)"
    )

    parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable performance profiling (for random mode)",
    )
    parser.add_argument(
        "--fps", type=int, default=60, help="Simulation FPS (for random mode)"
    )
    parser.add_argument(
        "--max-trials",
        type=int,
        default=20,
        help="Maximum number of trials to run (for random mode)",
    )

    args = parser.parse_args()

    if args.mode == "solutions":
        # Visualize all solutions from file, optionally filtered by level
        visualize_all_solutions(args.solutions, args.pause, args.max_viz, args.level)
    elif args.mode == "single":
        # Visualize a single solution
        if not args.level or args.seed is None:
            print("Error: --level and --seed are required for single solution mode")
            return
        visualize_solution_from_file(args.solutions, args.level, args.seed, args.pause)
    else:
        # Random mode (original functionality)
        if not args.level:
            print("Error: --level is required for random mode")
            return
        run_random_demo(args.level, args.seed, args.max_trials, args.fps, args.profile)


if __name__ == "__main__":
    main()
