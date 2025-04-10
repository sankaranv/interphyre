import random
import numpy as np
import phyre2
import argparse
import os
import yaml

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--level", type=str, default="tip_over_bar")
    parser.add_argument("--config_dir", type=str, default="./")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--num_trials", type=int, default=10)
    parser.add_argument("--with_solution", type=bool, default=True)
    args = parser.parse_args()

    # Set seed
    np.random.seed(args.seed)
    random.seed(args.seed)

    # Load the simulator config from YAML
    config = yaml.load(
        open(os.path.join(args.config_dir, "config.yaml"), "r"), Loader=yaml.FullLoader
    )

    # Load the level
    print(args.level)
    level = phyre2.PHYRELevel()
    level.load_from_file(args.level, args.with_solution)

    # Create the simulator
    env = phyre2.PHYREWorld(level, render_level=True, render_mode="pygame")

    # # Take random actions
    # for i in range(args.num_trials):
    #     action = env.action_space.sample()
    #     observation, reward, done, info = env.step(action)
    #     termination = info["termination"]
    #     print(f"Trial {i} reward: {reward} termination condition: {termination}")
    #     env.reset()

    action = level.solution
    observation, reward, done, info = env.step(action)
    termination = info["termination"]
    print(
        f"Trial {args.num_trials} reward: {reward} termination condition: {termination}"
    )
    env.reset()
