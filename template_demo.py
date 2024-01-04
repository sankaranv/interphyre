import phyre2
import argparse
import os
import yaml

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_dir", type=str, default="./")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--num_trials", type=int, default=10)
    parser.add_argument("--with_solution", type=bool, default=True)
    parser.add_argument("--task", type=str)
    args = parser.parse_args()

    # Set random seed
    phyre2.set_seed(args.seed)

    # Create template and generate a random level
    template = phyre2.tasks.get_task(args.task)
    levels = template.generate_random_levels(
        10, check_solvable=False, save_to_file=False
    )

    # Set up the simulator
    config = yaml.load(
        open(os.path.join(args.config_dir, "config.yaml"), "r"), Loader=yaml.FullLoader
    )

    if not levels:
        print("No levels generated")
        exit()

    # Solve the level
    for level in levels:
        print(f"Level: {level['name']}")
        env = phyre2.PHYREWorld(
            phyre2.PHYRELevel(level),
            fps=config["fps"],
            screen_size=config["screen_size"],
            vel_iters=config["vel_iters"],
            pos_iters=config["pos_iters"],
            max_steps=config["max_steps"],
            render_level=True,
            render_mode="pygame",
        )
        action = env.action_space.sample()
        print(action)
        obs, reward, done, info = env.step(action)
        termination = info["termination"]
        print(f"Reward: {reward} Termination condition: {termination}")
        env.reset()
