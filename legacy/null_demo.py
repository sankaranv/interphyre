import random
import numpy as np
import phyre2
import argparse
import os
import yaml

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--level", type=str, default="demo/level_2")
    parser.add_argument("--config_dir", type=str, default="./")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--num_trials", type=int, default=10)
    parser.add_argument("--with_solution", type=bool, default=True)
    args = parser.parse_args()

    # Set seed
    # np.random.seed(args.seed)
    # random.seed(args.seed)

    # Load the simulator config from YAML
    config = yaml.load(
        open(os.path.join(args.config_dir, "config.yaml"), "r"), Loader=yaml.FullLoader
    )

    # Load the level
    level = phyre2.PHYRELevel()
    level.load_from_file(args.level, args.with_solution)

    # Create the simulator
    env = phyre2.PHYREWorld(
        level,
        fps=config["fps"],
        screen_size=config["screen_size"],
        vel_iters=config["vel_iters"],
        pos_iters=config["pos_iters"],
        max_steps=config["max_steps"],
        render_level=True,
        render_mode="pygame",
    )

    # Use the solution provided to complete the task
    action = level.solution
    observation, reward, done, info = env.step(action)
    termination = info["termination"]
    print(f"Before null => Reward: {reward} termination condition: {termination}")
    env.reset()

    # Null out a random object that is not action, target, or goal
    free_objects = [
        obj
        for obj in level.objects
        if obj not in [level.target_object, level.goal_object] + level.action_objects
    ]
    # Sample two objects without replacement
    null_objects = random.sample(free_objects, 2)
    print(f"Nulling out objects: {null_objects}")
    for obj in null_objects:
        level.null_object(obj, env)

    # Run the environment again
    action = env.action_space.sample()
    observation, reward, done, info = env.step(action)
    termination = info["termination"]
    print(f"After null => reward: {reward} termination condition: {termination}")

    # Restore nulled objects
    print(f"Restoring object {obj}")
    level.restore_nulled_objects(env)

    # Run the environment again
    action = level.solution
    observation, reward, done, info = env.step(action)
    termination = info["termination"]
    print(f"After restore => reward: {reward} termination condition: {termination}")
