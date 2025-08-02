#!/usr/bin/env python3
"""
Test script for clean agents (DQN and PPO) without domain knowledge.

This script tests whether agents can learn purely from state information
without any reward shaping or domain knowledge.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import time
from typing import Dict, Any, List, Optional
from interphyre.environment import PhyreEnv
from interphyre.levels import load_level
from agents import CleanDQNAgent, PPOAgent
from tools.train_agent import TrainingLoop


def test_clean_agents(
    level_name: str = "down_to_earth",
    num_episodes: int = 50,
    max_trials: int = 20,
    seeds: Optional[List[int]] = None,
):
    """
    Test clean agents (no domain knowledge) on a level.

    Args:
        level_name: Name of the level to test
        num_episodes: Number of episodes per agent
        max_trials: Maximum trials per episode
        seeds: List of seeds for reproducibility
    """
    if seeds is None:
        seeds = list(range(42, 42 + num_episodes))

    # Create clean agents (no domain knowledge)
    agents = {
        "Clean DQN": CleanDQNAgent(
            name="clean_dqn",
            seed=42,
            learning_rate=1e-3,
            gamma=0.99,
            epsilon=1.0,
            epsilon_min=0.01,
            epsilon_decay=0.995,
            memory_size=10000,
            batch_size=32,
            target_update=100,
            hidden_size=128,
            noise_std=0.1,
        ),
        "PPO": PPOAgent(
            name="ppo",
            seed=42,
            learning_rate=3e-4,
            gamma=0.99,
            gae_lambda=0.95,
            clip_ratio=0.2,
            value_loss_coef=0.5,
            entropy_coef=0.01,
            max_grad_norm=0.5,
            hidden_size=128,
            buffer_size=2048,
            batch_size=64,
            epochs_per_update=10,
        ),
    }

    results = {}

    print(f"Testing clean agents (no domain knowledge) on {level_name} level...")
    print(f"Episodes per agent: {num_episodes}")
    print(f"Max trials per episode: {max_trials}")
    print("=" * 60)

    for agent_name, agent in agents.items():
        print(f"\nTesting {agent_name} agent...")
        print("-" * 40)

        # Create training loop
        trainer = TrainingLoop(
            level_name=level_name,
            agent=agent,
            max_trials=max_trials,
            max_steps_per_trial=1000,
            verbose=False,  # Less verbose for testing
        )

        # Train and get results
        stats = trainer.train(num_episodes=num_episodes, seeds=seeds)
        results[agent_name] = stats

        print(f"  Success rate: {stats['success_rate']:.2%}")
        print(f"  Avg trials per episode: {stats['avg_trials_per_episode']:.1f}")
        print(f"  Avg episode time: {stats['avg_episode_time']:.3f}s")

        # Show training progress
        episode_stats = stats["episode_stats"]
        print(f"  Training progress:")
        print(
            f"    Episodes 1-10:   {np.mean([s['success'] for s in episode_stats[:10]]):.1%} success"
        )
        print(
            f"    Episodes 11-20:  {np.mean([s['success'] for s in episode_stats[10:20]]):.1%} success"
        )
        print(
            f"    Episodes 21-30:  {np.mean([s['success'] for s in episode_stats[20:30]]):.1%} success"
        )
        print(
            f"    Episodes 31-40:  {np.mean([s['success'] for s in episode_stats[30:40]]):.1%} success"
        )
        print(
            f"    Episodes 41-50:  {np.mean([s['success'] for s in episode_stats[40:50]]):.1%} success"
        )

    # Print comparison summary
    print("\n" + "=" * 60)
    print("CLEAN AGENTS COMPARISON SUMMARY")
    print("=" * 60)

    for agent_name, stats in results.items():
        print(
            f"{agent_name:12} | Success: {stats['success_rate']:6.1%} | "
            f"Avg Trials: {stats['avg_trials_per_episode']:5.1f} | "
            f"Avg Time: {stats['avg_episode_time']:6.3f}s"
        )

    print("=" * 60)

    # Find best performing agent
    best_agent = max(results.items(), key=lambda x: x[1]["success_rate"])
    print(
        f"\nBest performing clean agent: {best_agent[0]} ({best_agent[1]['success_rate']:.1%} success rate)"
    )

    return results


def test_learning_curves(level_name: str = "down_to_earth", num_episodes: int = 100):
    """
    Test learning curves for clean agents over more episodes.

    Args:
        level_name: Name of the level to test
        num_episodes: Number of episodes for learning curve
    """
    print(f"\nTesting learning curves for clean agents...")
    print(f"Episodes: {num_episodes}")
    print("=" * 60)

    # Test PPO with more episodes
    ppo_agent = PPOAgent(
        name="ppo_learning_curve",
        seed=42,
        learning_rate=3e-4,
        gamma=0.99,
        gae_lambda=0.95,
        clip_ratio=0.2,
        value_loss_coef=0.5,
        entropy_coef=0.01,
        max_grad_norm=0.5,
        hidden_size=128,
        buffer_size=2048,
        batch_size=64,
        epochs_per_update=10,
    )

    trainer = TrainingLoop(
        level_name=level_name,
        agent=ppo_agent,
        max_trials=15,
        max_steps_per_trial=1000,
        verbose=False,
    )

    # Train with progress tracking
    seeds = list(range(42, 42 + num_episodes))
    episode_stats = []

    print("Training PPO agent...")
    for i in range(0, num_episodes, 10):
        batch_seeds = seeds[i : i + 10]
        stats = trainer.train(num_episodes=len(batch_seeds), seeds=batch_seeds)
        episode_stats.extend(stats["episode_stats"])

        success_rate = np.mean([s["success"] for s in episode_stats])
        avg_trials = np.mean([s["trials"] for s in episode_stats])

        print(
            f"  Episodes {i+1}-{i+len(batch_seeds)}: {success_rate:.1%} success, {avg_trials:.1f} avg trials"
        )

    print(
        f"\nFinal PPO results: {success_rate:.1%} success rate, {avg_trials:.1f} avg trials"
    )

    return episode_stats


def main():
    """Main test function."""
    # Test clean agents
    results = test_clean_agents(
        level_name="down_to_earth",
        num_episodes=50,
        max_trials=20,
        seeds=list(range(42, 92)),
    )

    # Test learning curves
    learning_curve = test_learning_curves(level_name="down_to_earth", num_episodes=100)

    return results, learning_curve


if __name__ == "__main__":
    main()
