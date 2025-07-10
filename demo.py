import argparse
import numpy as np
from interphyre.levels import load_level
from interphyre.environment import PhyreEnv
from interphyre.render.pygame import PygameRenderer
from interphyre.config import SimulationConfig


def main():
    parser = argparse.ArgumentParser(description="Interphyre Demo Script")
    parser.add_argument(
        "--task",
        type=str,
        default="two_body_problem",
        help="Level name to run",
    )
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument(
        "--profile", action="store_true", help="Enable performance profiling"
    )
    parser.add_argument("--fps", type=int, default=60, help="Simulation FPS")
    parser.add_argument(
        "--max_trials", type=int, default=20, help="Maximum number of trials to run"
    )
    args = parser.parse_args()

    # Create configuration with performance profiling if requested
    config = SimulationConfig(
        fps=args.fps,
        time_step=1 / args.fps,
        enable_profiling=args.profile,
        log_step_times=args.profile,
    )

    # Instantiate the renderer
    renderer = PygameRenderer(width=600, height=600, ppm=60)

    trial = 0
    success = False
    while trial < args.max_trials:
        trial += 1
        seed = np.random.randint(0, 100000) if args.seed is None else args.seed
        level = load_level(args.task, seed=seed)
        env = PhyreEnv(level=level, renderer=renderer, config=config)

        # Reset the environment. This instantiates the Box2DEngine and loads level objects.
        obs, info = env.reset()

        # For the demo, we assume the level has action objects (e.g., "red_ball" in a touch_ball task)
        # Here, we provide dummy actions (e.g. not moving them, or you can adjust as needed)
        action_x = np.random.uniform(-4.5, 4.5)
        action_y = np.random.uniform(-2, 4)
        action = [(action_x, action_y) for _ in level.action_objects]

        # Execute a step to apply the action (which is only placed once) and advance the simulation.
        obs, reward, done, truncated, info = env.step(action)

        # Run additional simulation steps (if needed).
        trace = env.simulate(steps=500, return_trace=True)

        if trace[-1][1]:
            print(f"Success!")

            # Print performance stats if profiling was enabled
            if args.profile:
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
        print(f"No success after {args.max_trials} trials.")

    # Render the final state to the screen for a short period before closing.
    renderer.wait(500)
    env.close()


if __name__ == "__main__":
    main()
