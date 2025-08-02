import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import argparse
import json
from interphyre.levels import load_level
from interphyre.environment import PhyreEnv
from interphyre.render.pygame import PygameRenderer
from interphyre.config import SimulationConfig
import time


def main():
    parser = argparse.ArgumentParser(
        description="Visualize a list of solutions for various levels and seeds."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to JSON file with solutions list.",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=2.0,
        help="Seconds to pause between visualizations.",
    )
    args = parser.parse_args()

    # Load the list of solutions
    with open(args.input, "r") as f:
        solution_list = json.load(f)

    config = SimulationConfig(fps=60, time_step=1 / 60, enable_profiling=False)

    for entry in solution_list:
        level_name = entry["level"]
        seed = entry["seed"]
        action = entry["solution"]
        print(f"Visualizing: {level_name}, seed {seed}, action {action}")

        renderer = PygameRenderer(width=600, height=600, ppm=60)
        level = load_level(level_name, seed=seed)
        env = PhyreEnv(level=level, renderer=renderer, config=config)

        obs, info = env.reset()
        obs, reward, done, truncated, info = env.step(action)
        trace = env.simulate(steps=500, return_trace=True)
        success = False
        if trace and isinstance(trace[-1][4], dict):
            success = trace[-1][4].get("success", False)
        print(f"  Success: {success}")

        time.sleep(args.pause)
        env.close()
        renderer.close()


if __name__ == "__main__":
    main()
