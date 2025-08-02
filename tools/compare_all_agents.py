#!/usr/bin/env python3
"""
Comprehensive agent comparison script for Interphyre.

This script compares all available agents on the down_to_earth level
including random, heuristic, DQN, and continuous DQN agents.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import time
from typing import Dict, Any, List, Optional
from interphyre.environment import PhyreEnv
from interphyre.levels import load_level
from agents import RandomAgent, HeuristicAgent, DQNAgent, ContinuousDQNAgent
from tools.train_agent import TrainingLoop


def compare_all_agents(
    level_name: str = "down_to_earth",
    num_episodes: int = 20,
    max_trials: int = 15,
    seeds: Optional[List[int]] = None,
):
    """
    Compare all available agents on a level.

    Args:
        level_name: Name of the level to test
        num_episodes: Number of episodes per agent
        max_trials: Maximum trials per episode
        seeds: List of seeds for reproducibility
    """
    if seeds is None:
        seeds = list(range(42, 42 + num_episodes))

    # Create agents
    agents = {
        "Random": RandomAgent(name="random", seed=42),
        "Heuristic": HeuristicAgent(name="heuristic", seed=42),
        "DQN": DQNAgent(name="dqn", seed=42),
        "Continuous DQN": ContinuousDQNAgent(name="continuous_dqn", seed=42),
    }

    results = {}

    print(f"Comparing all agents on {level_name} level...")
    print(f"Episodes per agent: {num_episodes}")
    print(f"Max trials per episode: {max_trials}")
    print()

    for agent_name, agent in agents.items():
        print(f"Testing {agent_name} agent...")

        # Create training loop
        trainer = TrainingLoop(
            level_name=level_name,
            agent=agent,
            max_trials=max_trials,
            max_steps_per_trial=1000,
            verbose=False,  # Less verbose for comparison
        )

        # Train and get results
        stats = trainer.train(num_episodes=num_episodes, seeds=seeds)
        results[agent_name] = stats

        print(f"  Success rate: {stats['success_rate']:.2%}")
        print(f"  Avg trials per episode: {stats['avg_trials_per_episode']:.1f}")
        print(f"  Avg episode time: {stats['avg_episode_time']:.3f}s")

        # For RL agents, show additional info
        if hasattr(agent, "epsilon"):
            print(f"  Final epsilon: {agent.epsilon:.3f}")
        if hasattr(agent, "step_count"):
            print(f"  Training steps: {agent.step_count}")
        print()

    # Print comparison summary
    print("=" * 70)
    print("COMPREHENSIVE COMPARISON SUMMARY")
    print("=" * 70)

    for agent_name, stats in results.items():
        print(
            f"{agent_name:16} | Success: {stats['success_rate']:6.1%} | "
            f"Avg Trials: {stats['avg_trials_per_episode']:5.1f} | "
            f"Avg Time: {stats['avg_episode_time']:6.3f}s"
        )

    print("=" * 70)

    # Find best performing agent
    best_agent = max(results.items(), key=lambda x: x[1]["success_rate"])
    print(
        f"\nBest performing agent: {best_agent[0]} ({best_agent[1]['success_rate']:.1%} success rate)"
    )

    return results


def test_trained_agents(level_name: str = "down_to_earth", num_episodes: int = 10):
    """
    Test pre-trained agents if available.

    Args:
        level_name: Name of the level to test
        num_episodes: Number of episodes per agent
    """
    print(f"\nTesting pre-trained agents on {level_name} level...")
    print("=" * 50)

    # Test continuous DQN if model exists
    continuous_dqn_path = "models/continuous_dqn_down_to_earth.pth"
    if os.path.exists(continuous_dqn_path):
        print("Testing pre-trained Continuous DQN agent...")

        agent = ContinuousDQNAgent(name="trained_continuous_dqn", seed=42)
        agent.load(continuous_dqn_path)
        agent.set_training(False)  # Evaluation mode

        trainer = TrainingLoop(
            level_name=level_name,
            agent=agent,
            max_trials=10,
            max_steps_per_trial=1000,
            verbose=False,
        )

        stats = trainer.train(
            num_episodes=num_episodes, seeds=list(range(3000, 3000 + num_episodes))
        )

        print(f"  Pre-trained success rate: {stats['success_rate']:.2%}")
        print(f"  Pre-trained avg trials: {stats['avg_trials_per_episode']:.1f}")
    else:
        print("No pre-trained Continuous DQN model found.")

    # Test DQN if model exists
    dqn_path = "models/dqn_down_to_earth.pth"
    if os.path.exists(dqn_path):
        print("Testing pre-trained DQN agent...")

        agent = DQNAgent(name="trained_dqn", seed=42)
        agent.load(dqn_path)
        agent.set_training(False)  # Evaluation mode

        trainer = TrainingLoop(
            level_name=level_name,
            agent=agent,
            max_trials=10,
            max_steps_per_trial=1000,
            verbose=False,
        )

        stats = trainer.train(
            num_episodes=num_episodes, seeds=list(range(4000, 4000 + num_episodes))
        )

        print(f"  Pre-trained success rate: {stats['success_rate']:.2%}")
        print(f"  Pre-trained avg trials: {stats['avg_trials_per_episode']:.1f}")
    else:
        print("No pre-trained DQN model found.")


def main():
    """Main comparison function."""
    # Compare all agents
    results = compare_all_agents(
        level_name="down_to_earth",
        num_episodes=15,  # Reasonable number for comparison
        max_trials=15,
        seeds=list(range(42, 57)),
    )

    # Test pre-trained agents
    test_trained_agents(level_name="down_to_earth", num_episodes=10)

    return results


if __name__ == "__main__":
    main()
