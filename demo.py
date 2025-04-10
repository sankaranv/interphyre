import argparse
import numpy as np
from phyre2.levels import load_level
from phyre2.environment import PhyreEnv
from phyre2.render.pygame import PygameRenderer
import numpy as np


def main():
    parser = argparse.ArgumentParser(description="Phyre2 Demo Script")
    parser.add_argument(
        "--task",
        type=str,
        default="touch_ball",
        help="Level name to run (default: touch_ball)",
    )
    parser.add_argument("--seed", type=int, help="Random seed")
    args = parser.parse_args()

    # Instantiate the renderer
    renderer = PygameRenderer(width=600, height=600, ppm=60)

    while True:

        seed = np.random.randint(0, 100000) if args.seed is None else args.seed
        level = load_level(args.task, seed=seed)
        env = PhyreEnv(level=level, renderer=renderer)

        # Reset the environment. This instantiates the Box2DEngine and loads level objects.
        obs, info = env.reset()

        # For the demo, we assume the level has action objects (e.g., "red_ball" in a touch_ball task)
        # Here, we provide dummy actions (e.g. not moving them, or you can adjust as needed)
        action_x = np.random.uniform(-4.0, 4.0)
        action_y = np.random.uniform(-2.0, 4.9)
        action = [(action_x, action_y) for _ in level.action_objects]

        # Execute a step to apply the action (which is only placed once) and advance the simulation.
        obs, reward, done, truncated, info = env.step(action)

        # Run additional simulation steps (if needed).
        trace = env.simulate(steps=500, return_trace=True)

        if trace[-1][1]:
            print(f"Success!")
            break

    # Render the final state to the screen for a short period before closing.
    renderer.wait(500)
    env.close()


if __name__ == "__main__":
    main()
