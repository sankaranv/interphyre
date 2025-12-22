import argparse
import json
import numpy as np
import os
import sys
from typing import Optional, List


# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from interphyre.levels import load_level
from interphyre.environment import PhyreEnv
from interphyre.render.pygame import PygameRenderer
from interphyre.config import SimulationConfig
from agents.random_agent import RandomAgent
from tools.video_recorder import VideoRecorder, generate_video_filename


def visualize_solution_from_file(
    solutions_file: str,
    level_name: str,
    seed: int,
    pause_time: float = 2.0,
    record_video: bool = False,
    video_format: str = "mp4",
    video_fps: int = 30,
    output_dir: str = "outputs",
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

    # Determine label from solutions file path
    label = "success" if "successes.json" in solutions_file else "failure"

    # Create configuration
    sim_fps = 60
    config = SimulationConfig(fps=sim_fps, time_step=1 / sim_fps, enable_profiling=False)

    # Create renderer (VideoRecorder for recording, PygameRenderer otherwise)
    if record_video:
        video_path = generate_video_filename(
            level_name, seed, output_dir, video_format, label=label
        )
        # Match video FPS to simulation FPS to avoid slow motion
        renderer = VideoRecorder(
            width=600, height=600, ppm=60, video_format=video_format, fps=sim_fps
        )
        renderer.set_output_path(video_path)
        print(f"Recording video to: {video_path}")
    else:
        renderer = PygameRenderer(width=600, height=600, ppm=60)

    try:
        # Load level and create environment
        level = load_level(level_name, seed=seed)
        env = PhyreEnv(level=level, renderer=renderer, config=config)

        # Reset environment
        obs, info = env.reset()

        # Apply action and run full simulation to completion
        obs, reward, terminated, truncated, info = env.step(action)

        # Check success from the final step result
        success = info.get("success", False)

        print(f"Success: {success}")

        # Pause to show the result (only if not recording)
        if not record_video:
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
    seed_filter: Optional[List[int]] = None,
    record_video: bool = False,
    video_format: str = "mp4",
    video_fps: int = 30,
    output_dir: str = "outputs",
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
    if record_video:
        print(f"Recording videos to: {output_dir}")
    print("-" * 60)

    # Collect all visualizations
    all_visualizations = []
    for level_name, level_data in solutions_data.items():
        # Skip if level filter is specified and doesn't match
        if level_filter and level_name != level_filter:
            continue
        for seed_str, action in level_data["solutions"].items():
            seed_val = int(seed_str)
            if seed_filter and seed_val not in seed_filter:
                continue
            all_visualizations.append((level_name, seed_val, action))

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
            solutions_file,
            level_name,
            seed,
            pause_time,
            record_video,
            video_format,
            video_fps,
            output_dir,
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
    cycle_seeds: bool = False,
    record_video: bool = False,
    video_format: str = "mp4",
    video_fps: int = 30,
    output_dir: str = "outputs",
):
    """Run demo with RandomAgent and invalid action rejection."""
    # Create configuration with performance profiling if requested
    config = SimulationConfig(
        fps=fps,
        time_step=1 / fps,
        enable_profiling=profile,
        log_step_times=profile,
    )

    # Create renderer (VideoRecorder for recording, PygameRenderer otherwise)
    if record_video:
        # For random mode, we'll record the successful trial or the last trial
        video_path = generate_video_filename(
            level_name, seed, output_dir, video_format, suffix="random"
        )
        # Match video FPS to simulation FPS to avoid slow motion
        renderer = VideoRecorder(
            width=600, height=600, ppm=60, video_format=video_format, fps=fps
        )
        renderer.set_output_path(video_path)
        print(f"Recording video to: {video_path}")
    else:
        renderer = PygameRenderer(width=600, height=600, ppm=60)

    # Create RandomAgent
    agent = RandomAgent(seed=seed)

    trial = 0
    success = False
    invalid_attempts = 0

    # Create environment once and reuse it
    trial_seed = np.random.randint(0, 100000) if seed is None else seed
    level = load_level(level_name, seed=trial_seed)
    env = PhyreEnv(level=level, renderer=renderer, config=config)

    while trial < max_trials:
        trial += 1

        try:
            # Use different seed for each trial if cycling is enabled
            if cycle_seeds:
                current_seed = trial_seed + trial
                level = load_level(level_name, seed=current_seed)
                env = PhyreEnv(level=level, renderer=renderer, config=config)

            # Clear video frames at start of each trial (only record one trial)
            # We'll record the successful trial, or the last trial if no success
            if record_video and hasattr(renderer, 'frames'):
                # Only clear if we haven't had a success yet
                # This way we keep the successful trial's frames
                if not success:
                    renderer.frames.clear()

            # Reset the environment
            obs, info = env.reset()

            # Set up the agent with the environment's action space
            agent.set_action_space(env.action_space)

            # Keep generating actions until we get a valid one
            max_attempts = 100  # Prevent infinite loops
            action = None
            for attempt in range(max_attempts):
                action = agent.get_action(obs)
                validation_result = env._validate_action_with_failure(action)
                if not validation_result["invalid"]:
                    break
                invalid_attempts += 1
            else:
                print(
                    f"Trial {trial}: Could not generate valid action after {max_attempts} attempts"
                )
                continue

            # Action is valid, run simulation
            obs, reward, terminated, truncated, info = env.step(action)

            # Print trial result
            print(
                f"Trial {trial}: terminated={terminated}, truncated={truncated}, reward={reward}"
            )

            if terminated and reward > 0:  # Success (positive reward)
                print(f"Success on trial {trial}!")
                success = True
                
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
                                for pair, counts in contact_stats[
                                    "pair_counts"
                                ].items():
                                    print(f"    {pair}: {counts}")
                
                # Stop recording after successful trial (only record one trial)
                if record_video:
                    break
                break
            elif terminated and reward < 0:  # Failure (negative reward)
                print(f"Trial {trial}: Failed (reward: {reward})")

        except Exception as e:
            print(f"Trial {trial}: Error - {e}")
            invalid_attempts += 1

    # Print summary
    print(f"\n{'='*50}")
    print(f"RANDOM AGENT DEMO SUMMARY")
    print(f"{'='*50}")
    print(f"Level: {level_name}")
    print(f"Valid trials completed: {trial}")
    print(f"Invalid action attempts: {invalid_attempts}")
    print(f"Success: {'Yes' if success else 'No'}")
    if not success:
        print(f"No success after {max_trials} valid trials.")

    # Close environment and renderer
    env.close()
    if not record_video:
        renderer.wait(500)
    renderer.close()


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
    parser.add_argument(
        "--seeds",
        nargs="*",
        type=int,
        help="Only visualize these seeds from the solutions file (solutions mode)",
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
    parser.add_argument(
        "--cycle-seeds",
        action="store_true",
        help="Use different seeds for each trial (generates new level variations)",
    )

    # Video recording options
    parser.add_argument(
        "--record-video",
        action="store_true",
        help="Record simulation as video instead of displaying with pygame (headless mode)",
    )
    parser.add_argument(
        "--video-format",
        type=str,
        choices=["mp4", "gif"],
        default="mp4",
        help="Video output format: mp4 or gif (default: mp4)",
    )
    parser.add_argument(
        "--video-fps",
        type=int,
        default=30,
        help="Target frames per second for video output (default: 30)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Base output directory for video files (default: outputs/). Videos will be saved in outputs/mp4/ or outputs/gif/",
    )

    args = parser.parse_args()

    if args.mode == "solutions":
        # Visualize all solutions from file, optionally filtered by level
        visualize_all_solutions(
            args.solutions,
            args.pause,
            args.max_viz,
            args.level,
            args.seeds,
            args.record_video,
            args.video_format,
            args.video_fps,
            args.output_dir,
        )
    elif args.mode == "single":
        # Visualize a single solution
        if not args.level or args.seed is None:
            print("Error: --level and --seed are required for single solution mode")
            return
        visualize_solution_from_file(
            args.solutions,
            args.level,
            args.seed,
            args.pause,
            args.record_video,
            args.video_format,
            args.video_fps,
            args.output_dir,
        )
    else:
        # Random mode
        if not args.level:
            print("Error: --level is required for random mode")
            return
        run_random_demo(
            args.level,
            args.seed,
            args.max_trials,
            args.fps,
            args.profile,
            args.cycle_seeds,
            args.record_video,
            args.video_format,
            args.video_fps,
            args.output_dir,
        )


if __name__ == "__main__":
    main()
