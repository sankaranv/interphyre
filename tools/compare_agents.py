#!/usr/bin/env python3
"""
Agent comparison script for Interphyre.

This script compares different agents on the down_to_earth level
to demonstrate the training infrastructure.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import time
from typing import Dict, Any, List
from interphyre.environment import PhyreEnv
from interphyre.levels import load_level
from agents import RandomAgent, HeuristicAgent
from tools.train_agent import TrainingLoop


def compare_agents(
    level_name: str = "down_to_earth",
    num_episodes: int = 10,
    max_trials: int = 20,
    seeds: List[int] = None,
):
    """
    Compare different agents on a level.

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
    }

    results = {}

    print(f"Comparing agents on {level_name} level...")
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
        print()

    # Print comparison summary
    print("=" * 50)
    print("COMPARISON SUMMARY")
    print("=" * 50)

    for agent_name, stats in results.items():
        print(
            f"{agent_name:12} | Success: {stats['success_rate']:6.1%} | "
            f"Avg Trials: {stats['avg_trials_per_episode']:5.1f} | "
            f"Avg Time: {stats['avg_episode_time']:6.3f}s"
        )

    print("=" * 50)

    return results


def main():
    """Main comparison function."""
    # Compare agents on down_to_earth level
    results = compare_agents(
        level_name="down_to_earth",
        num_episodes=10,
        max_trials=20,
        seeds=list(range(42, 52)),
    )

    return results


if __name__ == "__main__":
    main()
