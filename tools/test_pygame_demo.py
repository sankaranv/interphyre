#!/usr/bin/env python3
"""
Test script for pygame agent demo.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import PPOAgent
from tools.agent_demo import demo_agent


def main():
    """Test pygame demo with PPO agent."""
    print("Testing pygame demo with PPO agent...")

    # Create PPO agent
    agent = PPOAgent(
        name="ppo_pygame_test", seed=42, learning_rate=3e-4, gamma=0.99, hidden_size=128
    )

    # Set to evaluation mode
    agent.set_training(False)

    # Run demo with pygame
    results = demo_agent(
        agent_name="PPO",
        agent=agent,
        level_name="down_to_earth",
        num_demos=2,  # Just 2 episodes for testing
        max_trials=5,  # Fewer trials for testing
        show_details=True,
        use_pygame=True,
        fps=30,  # Lower FPS for testing
        pause_time=0.5,  # Shorter pause
    )

    print(f"\nDemo completed!")
    print(f"Success rate: {results['success_rate']:.1%}")
    print(f"Average trials: {results['avg_trials']:.1f}")

    # Save the agent after the demo
    agent.save("ppo_agent_demo.pth")
    print("Agent saved to ppo_agent_demo.pth")


if __name__ == "__main__":
    main()
