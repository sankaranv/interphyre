import phyre2
import argparse
import os
import yaml

if __name__ == "__main__":

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--level", type=str)
    parser.add_argument("--config_dir", type=str, default="./")
    args = parser.parse_args()

    # Load the simulator config from YAML
    config = yaml.load(open(os.path.join(args.config_dir, "config.yaml"), "r"), Loader=yaml.FullLoader)

    # Load the level
    level = phyre2.Level(ppm=config["ppm"])
    level.load(args.level)

    # Create the environment
    env = phyre2.PhyreEnv(level,
                          fps=config["fps"],
                          screen_size=config["screen_size"],
                          vel_iters=config["vel_iters"],
                          pos_iters=config["pos_iters"],
                          max_steps=config["max_steps"],
                          render_level=True)

    # Take random actions
    num_trials = 10
    for i in range(num_trials):
        action = env.action_space.sample()
        observation, reward, done, info = env.step(action)
        termination = info["termination"]
        print(f"Trial {i} reward: {reward} termination condition: {termination}")
        env.reset()

    action = level.solution
    observation, reward, done, info = env.step(action)
    termination = info["termination"]
    print(f"Trial {num_trials} reward: {reward} termination condition: {termination}")
    env.reset()
