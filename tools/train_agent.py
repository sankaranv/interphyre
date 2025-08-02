#!/usr/bin/env python3
"""
Agent training script for Interphyre.

This script demonstrates how to train agents using the PhyreEnv as a standard
gym environment. It implements the episode structure described in the requirements:
- Place action objects (x, y, size)
- Run simulation until success/failure
- Repeat until success or max trials
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import time
from typing import Dict, Any, Optional
from interphyre.environment import PhyreEnv
from interphyre.levels import load_level
from agents import RandomAgent


class TrainingLoop:
    """
    Training loop for agents on Interphyre levels.

    This implements the standard training loop where:
    1. Agent places action objects
    2. Simulation runs until success/failure
    3. Process repeats until success or max trials
    """

    def __init__(
        self,
        level_name: str,
        agent,
        max_trials: int = 100,
        max_steps_per_trial: int = 1000,
        verbose: bool = True,
    ):
        """
        Initialize the training loop.

        Args:
            level_name: Name of the level to train on
            agent: Agent to train
            max_trials: Maximum number of trials per episode
            max_steps_per_trial: Maximum steps per trial
            verbose: Whether to print progress
        """
        self.level_name = level_name
        self.agent = agent
        self.max_trials = max_trials
        self.max_steps_per_trial = max_steps_per_trial
        self.verbose = verbose

        # Create environment
        level = load_level(level_name)
        self.env = PhyreEnv(
            level=level,
            config=None,  # Use default config
            observation_type="physics_state",
            action_type="continuous",
        )

        # Training statistics
        self.episode_count = 0
        self.total_trials = 0
        self.successful_trials = 0
        self.episode_lengths = []

    def train_episode(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Train for one episode (until success or max trials).

        Args:
            seed: Random seed for the episode

        Returns:
            Dictionary with episode statistics
        """
        # Reset environment and agent ONCE per episode
        observation, info = self.env.reset(seed=seed)
        self.agent.reset()

        trial_count = 0
        total_steps = 0
        start_time = time.time()

        if self.verbose:
            print(f"Starting episode {self.episode_count + 1}")

        while trial_count < self.max_trials:
            trial_count += 1

            if self.verbose:
                print(f"  Trial {trial_count}/{self.max_trials}")

            # Agent chooses action (places objects)
            action = self.agent.act(observation)

            # Use the same observation for this trial (no reset)
            trial_observation = observation

            # Run complete episode with this action
            success, steps_taken, info = self.env.run_episode(
                action, max_steps=self.max_steps_per_trial
            )
            total_steps += steps_taken

            # Get final observation for RL update
            final_observation = self.env._get_observation()

            # Calculate reward for RL agent
            reward = 1.0 if success else 0.0

            # Update RL agent if it has an update method
            if hasattr(self.agent, "update"):
                self.agent.update(
                    observation=trial_observation,
                    action=action,
                    reward=reward,
                    next_observation=final_observation,
                    terminated=success,
                    truncated=False,
                    info=info,
                )

            if self.verbose:
                print(f"    Steps: {steps_taken}, Success: {success}")

            # Check if we succeeded
            if success:
                self.successful_trials += 1
                episode_length = trial_count
                self.episode_lengths.append(episode_length)

                if self.verbose:
                    print(f"  SUCCESS! Completed in {trial_count} trials")

                break
            else:
                if self.verbose:
                    print(f"  Trial {trial_count} failed")

        # Episode finished
        self.episode_count += 1
        self.total_trials += trial_count
        episode_time = time.time() - start_time

        # Calculate statistics
        success = trial_count < self.max_trials
        episode_stats = {
            "episode": self.episode_count,
            "success": success,
            "trials": trial_count,
            "total_steps": total_steps,
            "time": episode_time,
            "success_rate": self.successful_trials / self.episode_count,
            "avg_episode_length": (
                np.mean(self.episode_lengths) if self.episode_lengths else 0
            ),
        }

        if self.verbose:
            print(f"Episode {self.episode_count} finished:")
            print(f"  Success: {success}")
            print(f"  Trials: {trial_count}")
            print(f"  Time: {episode_time:.2f}s")
            print(f"  Overall success rate: {episode_stats['success_rate']:.2%}")
            print()

        return episode_stats

    def train(self, num_episodes: int, seeds: Optional[list] = None) -> Dict[str, Any]:
        """
        Train for multiple episodes.

        Args:
            num_episodes: Number of episodes to train
            seeds: List of seeds for each episode (optional)

        Returns:
            Dictionary with training statistics
        """
        if seeds is None:
            seeds = [None] * num_episodes

        episode_stats = []

        for i in range(num_episodes):
            stats = self.train_episode(seed=seeds[i])
            episode_stats.append(stats)

        # Calculate overall statistics
        overall_stats = {
            "total_episodes": num_episodes,
            "successful_episodes": sum(
                1 for stats in episode_stats if stats["success"]
            ),
            "success_rate": sum(1 for stats in episode_stats if stats["success"])
            / num_episodes,
            "avg_trials_per_episode": np.mean(
                [stats["trials"] for stats in episode_stats]
            ),
            "avg_episode_time": np.mean([stats["time"] for stats in episode_stats]),
            "episode_stats": episode_stats,
        }

        if self.verbose:
            print("Training completed!")
            print(f"Overall success rate: {overall_stats['success_rate']:.2%}")
            print(
                f"Average trials per episode: {overall_stats['avg_trials_per_episode']:.1f}"
            )
            print(f"Average episode time: {overall_stats['avg_episode_time']:.2f}s")

        return overall_stats


def main():
    """Main training function."""
    # Create a random agent
    agent = RandomAgent(name="random_baseline", seed=42)

    # Create training loop for down_to_earth level
    trainer = TrainingLoop(
        level_name="down_to_earth",
        agent=agent,
        max_trials=50,  # Reasonable limit for training
        max_steps_per_trial=1000,
        verbose=True,
    )

    # Train for a few episodes
    print("Training random agent on down_to_earth level...")
    stats = trainer.train(num_episodes=5, seeds=[42, 43, 44, 45, 46])

    print("\nFinal Results:")
    print(f"Success rate: {stats['success_rate']:.2%}")
    print(f"Average trials per episode: {stats['avg_trials_per_episode']:.1f}")

    return stats


if __name__ == "__main__":
    main()
