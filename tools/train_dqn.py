#!/usr/bin/env python3
"""
DQN training script for Interphyre.

This script trains a DQN agent on the down_to_earth level with proper
hyperparameters and training loops.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import time
import json
from typing import Dict, Any, List
from interphyre.environment import PhyreEnv
from interphyre.levels import load_level
from agents import DQNAgent
from tools.train_agent import TrainingLoop


def train_dqn(
    level_name: str = "down_to_earth",
    num_episodes: int = 100,
    max_trials: int = 20,
    save_path: str = "dqn_model.pth",
    eval_interval: int = 10,
):
    """
    Train a DQN agent on a level.

    Args:
        level_name: Name of the level to train on
        num_episodes: Number of training episodes
        max_trials: Maximum trials per episode
        save_path: Path to save the trained model
        eval_interval: How often to evaluate the agent

    Returns:
        Training statistics
    """

    print(f"Training DQN agent on {level_name} level...")
    print(f"Episodes: {num_episodes}")
    print(f"Max trials per episode: {max_trials}")
    print()

    # Create DQN agent with appropriate hyperparameters
    agent = DQNAgent(
        name="dqn_trained",
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
    )

    # Create training loop
    trainer = TrainingLoop(
        level_name=level_name,
        agent=agent,
        max_trials=max_trials,
        max_steps_per_trial=1000,
        verbose=False,  # Less verbose for long training
    )

    # Training statistics
    training_stats = []
    eval_stats = []

    print("Starting training...")
    print("Episode | Success Rate | Avg Trials | Epsilon | Time")
    print("-" * 55)

    start_time = time.time()

    for episode in range(num_episodes):
        episode_start = time.time()

        # Train one episode
        stats = trainer.train_episode(seed=42 + episode)
        training_stats.append(stats)

        episode_time = time.time() - episode_start

        # Print progress
        if (episode + 1) % 5 == 0 or episode == 0:
            print(
                f"{episode + 1:7d} | {stats['success_rate']:11.1%} | "
                f"{stats['avg_episode_length']:10.1f} | "
                f"{agent.epsilon:7.3f} | {episode_time:4.1f}s"
            )

        # Evaluate periodically
        if (episode + 1) % eval_interval == 0:
            print(f"\nEvaluating agent at episode {episode + 1}...")

            # Set agent to evaluation mode
            agent.set_training(False)

            # Evaluate on a few episodes
            eval_trainer = TrainingLoop(
                level_name=level_name,
                agent=agent,
                max_trials=10,  # Shorter evaluation
                max_steps_per_trial=1000,
                verbose=False,
            )

            eval_stats_batch = []
            for eval_ep in range(5):
                eval_stat = eval_trainer.train_episode(seed=1000 + eval_ep)
                eval_stats_batch.append(eval_stat)

            # Calculate evaluation metrics
            eval_success_rate = np.mean([s["success"] for s in eval_stats_batch])
            eval_avg_trials = np.mean([s["trials"] for s in eval_stats_batch])

            eval_stats.append(
                {
                    "episode": episode + 1,
                    "success_rate": eval_success_rate,
                    "avg_trials": eval_avg_trials,
                    "epsilon": agent.epsilon,
                }
            )

            print(
                f"Evaluation: Success rate = {eval_success_rate:.1%}, "
                f"Avg trials = {eval_avg_trials:.1f}"
            )

            # Save model if it's performing well
            if eval_success_rate > 0.8:
                agent.save(save_path)
                print(f"Model saved to {save_path}")

            # Set agent back to training mode
            agent.set_training(True)
            print()

    total_time = time.time() - start_time

    # Final evaluation
    print("\nFinal evaluation...")
    agent.set_training(False)

    final_eval_trainer = TrainingLoop(
        level_name=level_name,
        agent=agent,
        max_trials=10,
        max_steps_per_trial=1000,
        verbose=False,
    )

    final_eval_stats = []
    for eval_ep in range(10):
        eval_stat = final_eval_trainer.train_episode(seed=2000 + eval_ep)
        final_eval_stats.append(eval_stat)

    final_success_rate = np.mean([s["success"] for s in final_eval_stats])
    final_avg_trials = np.mean([s["trials"] for s in final_eval_stats])

    # Save final model
    agent.save(save_path)

    # Compile results
    results = {
        "level_name": level_name,
        "num_episodes": num_episodes,
        "max_trials": max_trials,
        "total_time": total_time,
        "final_success_rate": final_success_rate,
        "final_avg_trials": final_avg_trials,
        "training_stats": training_stats,
        "eval_stats": eval_stats,
        "final_eval_stats": final_eval_stats,
        "agent_hyperparameters": {
            "learning_rate": agent.learning_rate,
            "gamma": agent.gamma,
            "epsilon": agent.epsilon,
            "epsilon_min": agent.epsilon_min,
            "epsilon_decay": agent.epsilon_decay,
            "memory_size": agent.memory_size,
            "batch_size": agent.batch_size,
            "target_update": agent.target_update,
            "hidden_size": agent.hidden_size,
        },
    }

    # Print final results
    print("\n" + "=" * 50)
    print("TRAINING COMPLETED")
    print("=" * 50)
    print(f"Level: {level_name}")
    print(f"Episodes: {num_episodes}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Final success rate: {final_success_rate:.1%}")
    print(f"Final avg trials: {final_avg_trials:.1f}")
    print(f"Model saved to: {save_path}")

    return results


def main():
    """Main training function."""
    # Train DQN agent
    results = train_dqn(
        level_name="down_to_earth",
        num_episodes=50,  # Start with fewer episodes for testing
        max_trials=20,
        save_path="models/dqn_down_to_earth.pth",
        eval_interval=10,
    )

    # Save results
    os.makedirs("results", exist_ok=True)
    with open("results/dqn_training_results.json", "w") as f:
        # Convert numpy types to native Python types for JSON serialization
        json_results = json.loads(
            json.dumps(
                results,
                default=lambda x: (
                    float(x)
                    if isinstance(x, np.floating)
                    else int(x) if isinstance(x, np.integer) else x
                ),
            )
        )
        json.dump(json_results, f, indent=2)

    print(f"\nResults saved to results/dqn_training_results.json")

    return results


if __name__ == "__main__":
    main()
