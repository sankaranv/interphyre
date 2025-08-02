import argparse
import numpy as np
from agents import PPOAgent
from interphyre.environment import PhyreEnv
from interphyre.levels import load_level
from interphyre.render.pygame import PygameRenderer
from interphyre.config import SimulationConfig


def train_ppo_episodic(
    level_name="down_to_earth",
    num_episodes=10,
    max_trials=20,
    seed_start=1000,
    visualize=False,
    test_episodes=3,
    test_trials=10,
    fps=60,
    pause_time=1.0,
):
    agent = PPOAgent(name="ppo_train_demo", seed=42)
    agent.set_training(True)

    for episode in range(num_episodes):
        seed = seed_start + episode
        level = load_level(level_name, seed=seed)
        env = PhyreEnv(level=level)
        obs, info = env.reset(seed=seed)
        agent.reset()

        print(f"\n=== Episode {episode+1} (seed={seed}) ===")
        success = False
        for trial in range(max_trials):
            action = agent.act(obs)
            trial_success, steps, next_obs = env.run_episode(action)
            reward = 1.0 if trial_success else 0.0
            agent.update(obs, action, reward, next_obs, trial_success, False, {})
            print(f"  Trial {trial+1}: Success={trial_success}, Steps={steps}")
            if trial_success:
                print(f"  ✅ Solved in {trial+1} trials!")
                success = True
                break
            obs = next_obs
        if not success:
            print(f"  ❌ Failed after {max_trials} trials.")
        agent.save("ppo_agent_latest.pth")

    print("\nTraining complete. Agent saved as ppo_agent_latest.pth")

    if visualize:
        print("\n=== Visualizing test seeds with Pygame ===")
        agent.set_training(False)
        for i in range(test_episodes):
            seed = seed_start + num_episodes + i
            level = load_level(level_name, seed=seed)
            config = SimulationConfig(
                fps=fps, time_step=1 / fps, enable_profiling=False
            )
            renderer = PygameRenderer(width=600, height=600, ppm=60)
            env = PhyreEnv(level=level, renderer=renderer, config=config)
            obs, info = env.reset(seed=seed)
            agent.reset()
            print(f"\n--- Test Episode {i+1} (seed={seed}) ---")
            for trial in range(test_trials):
                action = agent.act(obs)
                success, steps, next_obs = env.run_episode(action)
                print(f"  Trial {trial+1}: Success={success}, Steps={steps}")
                renderer.wait(int(pause_time * 1000))
                if success:
                    print(f"  ✅ Solved in {trial+1} trials!")
                    renderer.wait(int(pause_time * 2000))
                    break
                obs = next_obs
            else:
                print(f"  ❌ Failed after {test_trials} trials.")
                renderer.wait(int(pause_time * 2000))
            env.close()


def main():
    parser = argparse.ArgumentParser(
        description="Train PPO agent episodically and optionally visualize test seeds."
    )
    parser.add_argument(
        "--level", type=str, default="down_to_earth", help="Level name to train on."
    )
    parser.add_argument(
        "--episodes", type=int, default=10, help="Number of training episodes."
    )
    parser.add_argument(
        "--trials", type=int, default=20, help="Max trials per episode."
    )
    parser.add_argument(
        "--seed_start", type=int, default=1000, help="Starting seed for episodes."
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Visualize test seeds with Pygame after training.",
    )
    parser.add_argument(
        "--test_episodes",
        type=int,
        default=3,
        help="Number of test episodes to visualize.",
    )
    parser.add_argument(
        "--test_trials", type=int, default=10, help="Max trials per test episode."
    )
    parser.add_argument(
        "--fps", type=int, default=60, help="FPS for Pygame visualization."
    )
    parser.add_argument(
        "--pause_time",
        type=float,
        default=1.0,
        help="Pause time (seconds) between trials in visualization.",
    )
    args = parser.parse_args()

    train_ppo_episodic(
        level_name=args.level,
        num_episodes=args.episodes,
        max_trials=args.trials,
        seed_start=args.seed_start,
        visualize=args.visualize,
        test_episodes=args.test_episodes,
        test_trials=args.test_trials,
        fps=args.fps,
        pause_time=args.pause_time,
    )


if __name__ == "__main__":
    main()
