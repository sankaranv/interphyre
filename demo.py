import argparse
import pygame
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
    parser.add_argument("--seed", type=int, help="Random seed (default: 42)")
    args = parser.parse_args()

    # Load the level using the registry mechanism in levels/__init__.py
    seed = np.random.randint(0, 100000) if args.seed is None else args.seed
    level = load_level(args.task, seed=seed)

    # Instantiate the renderer and environment
    renderer = PygameRenderer(width=600, height=600, ppm=60)
    env = PhyreEnv(level=level, renderer=renderer)
    # Reset the environment. This instantiates the Box2DEngine and loads level objects.
    obs, info = env.reset()

    # For the demo, we assume the level has action objects (e.g., "red_ball" in a touch_ball task)
    # Here, we provide dummy actions (e.g. not moving them, or you can adjust as needed)
    action = [(0.0, 0.0) for _ in level.action_objects]

    # Print all objects in the level for debugging
    for obj_name, obj in level.objects.items():
        print(f"{obj_name}: {obj}")

    # Execute a step to apply the action (which is only placed once) and advance the simulation.
    obs, reward, done, truncated, info = env.step(action)

    # Run additional simulation steps (if needed).
    env.simulate(steps=1000)

    # Render the final state to the screen for a short period before closing.
    renderer.wait(1500)
    env.close()


if __name__ == "__main__":
    main()
