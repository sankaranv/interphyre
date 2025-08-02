#!/usr/bin/env python3
"""
Simple example of training an agent on Interphyre.

This script demonstrates the basic usage of the agent training system.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import RandomAgent, HeuristicAgent
from tools.train_agent import TrainingLoop


def main():
    """Demonstrate basic agent training."""

    print("Interphyre Agent Training Example")
    print("=" * 40)

    # Example 1: Train a random agent
    print("\n1. Training Random Agent")
    print("-" * 20)

    random_agent = RandomAgent(name="example_random", seed=123)

    trainer = TrainingLoop(
        level_name="down_to_earth",
        agent=random_agent,
        max_trials=10,
        max_steps_per_trial=500,
        verbose=True,
    )

    stats = trainer.train(num_episodes=3, seeds=[123, 124, 125])

    print(f"\nRandom Agent Results:")
    print(f"  Success rate: {stats['success_rate']:.1%}")
    print(f"  Average trials: {stats['avg_trials_per_episode']:.1f}")

    # Example 2: Train a heuristic agent
    print("\n\n2. Training Heuristic Agent")
    print("-" * 20)

    heuristic_agent = HeuristicAgent(name="example_heuristic", seed=123)

    trainer = TrainingLoop(
        level_name="down_to_earth",
        agent=heuristic_agent,
        max_trials=10,
        max_steps_per_trial=500,
        verbose=True,
    )

    stats = trainer.train(num_episodes=3, seeds=[123, 124, 125])

    print(f"\nHeuristic Agent Results:")
    print(f"  Success rate: {stats['success_rate']:.1%}")
    print(f"  Average trials: {stats['avg_trials_per_episode']:.1f}")

    print("\n" + "=" * 40)
    print("Training complete!")

    return stats


if __name__ == "__main__":
    main()
