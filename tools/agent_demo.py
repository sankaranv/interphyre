#!/usr/bin/env python3
"""
Agent demo script for Interphyre.

This script demonstrates how trained agents perform on new seeds,
showing their decision-making process and success rates.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import time
import random
from typing import Dict, Any, List, Optional
from interphyre.environment import PhyreEnv
from interphyre.levels import load_level
from interphyre.render.pygame import PygameRenderer
from interphyre.config import SimulationConfig
from agents import CleanDQNAgent, PPOAgent, RandomAgent, HeuristicAgent
from tools.train_agent import TrainingLoop


def demo_agent(
    agent_name: str,
    agent,
    level_name: str = "down_to_earth",
    num_demos: int = 10,
    max_trials: int = 15,
    show_details: bool = True,
    use_pygame: bool = False,
    fps: int = 60,
    pause_time: float = 1.0,
):
    """
    Demo a specific agent on new seeds.

    Args:
        agent_name: Name of the agent for display
        agent: The agent instance
        level_name: Level to test on
        num_demos: Number of demonstration episodes
        max_trials: Maximum trials per episode
        show_details: Whether to show detailed action information
    """
    print(f"\n{'='*60}")
    print(f"DEMO: {agent_name.upper()} AGENT")
    print(f"{'='*60}")
    print(f"Level: {level_name}")
    print(f"Episodes: {num_demos}")
    print(f"Max trials per episode: {max_trials}")
    print(f"Agent type: {type(agent).__name__}")

    # Create environment with optional pygame renderer
    level = load_level(level_name)

    if use_pygame:
        # Create configuration and renderer for visualization
        config = SimulationConfig(fps=fps, time_step=1 / fps, enable_profiling=False)
        from interphyre.render.pygame import PygameRenderer

        renderer = PygameRenderer(width=600, height=600, ppm=60)
        env = PhyreEnv(level=level, renderer=renderer, config=config)
        print(f"Using pygame visualization (FPS: {fps}, pause: {pause_time}s)")
    else:
        env = PhyreEnv(level=level)

    # Demo statistics
    successes = 0
    total_trials = 0
    episode_stats = []

    # Use new seeds for demo
    demo_seeds = list(range(1000, 1000 + num_demos))

    for episode in range(num_demos):
        seed = demo_seeds[episode]
        print(f"\n--- Episode {episode + 1} (Seed: {seed}) ---")

        # Reset environment with new seed
        env.reset(seed=seed)
        agent.reset()

        episode_success = False
        episode_trials = 0
        episode_actions = []

        for trial in range(max_trials):
            # Get current observation
            observation = env._get_observation()

            # Agent chooses action
            start_time = time.time()
            action = agent.act(observation)
            decision_time = time.time() - start_time

            if show_details:
                print(
                    f"  Trial {trial + 1}: Action = [{action[0]:.2f}, {action[1]:.2f}, {action[2]:.2f}] "
                    f"(decision time: {decision_time:.3f}s)"
                )

            # Run episode with this action
            success, steps, final_observation = env.run_episode(action)

            # Show pygame visualization if enabled
            if use_pygame and env.renderer is not None:
                from interphyre.render.pygame import PygameRenderer

                pygame_renderer = env.renderer  # type: ignore
                if success:
                    print(f"    ✅ SUCCESS! Completed in {steps} steps")
                    # Show success state for longer
                    pygame_renderer.wait(int(pause_time * 2000))
                else:
                    print(f"    ❌ Failed after {steps} steps")
                    # Show failure state briefly
                    pygame_renderer.wait(int(pause_time * 1000))

            # Update agent (if it's a learning agent)
            if hasattr(agent, "update"):
                agent.update(
                    observation,
                    action,
                    1.0 if success else 0.0,
                    final_observation,
                    success,
                    False,
                    {},
                )

            episode_trials += 1
            episode_actions.append(action.copy())

            if success:
                episode_success = True
                successes += 1
                if show_details:
                    print(f"    ✅ SUCCESS! Completed in {steps} steps")
                break
            else:
                if show_details:
                    print(f"    ❌ Failed after {steps} steps")

        total_trials += episode_trials

        if not episode_success:
            if show_details:
                print(f"    ❌ Episode failed after {episode_trials} trials")

        episode_stats.append(
            {
                "success": episode_success,
                "trials": episode_trials,
                "seed": seed,
                "actions": episode_actions,
            }
        )

        # Show episode summary
        status = "✅ SUCCESS" if episode_success else "❌ FAILED"
        print(f"  Episode {episode + 1} Result: {status} ({episode_trials} trials)")

    # Calculate statistics
    success_rate = successes / num_demos
    avg_trials = total_trials / num_demos

    print(f"\n{'='*60}")
    print(f"DEMO RESULTS: {agent_name.upper()}")
    print(f"{'='*60}")
    print(f"Success Rate: {success_rate:.1%} ({successes}/{num_demos})")
    print(f"Average Trials per Episode: {avg_trials:.1f}")
    print(f"Total Trials: {total_trials}")

    # Show action analysis
    if show_details and episode_stats:
        print(f"\nAction Analysis:")
        all_actions = []
        for stats in episode_stats:
            all_actions.extend(stats["actions"])

        if all_actions:
            actions_array = np.array(all_actions)
            print(
                f"  Average X position: {np.mean(actions_array[:, 0]):.2f} ± {np.std(actions_array[:, 0]):.2f}"
            )
            print(
                f"  Average Y position: {np.mean(actions_array[:, 1]):.2f} ± {np.std(actions_array[:, 1]):.2f}"
            )
            print(
                f"  Average ball size: {np.mean(actions_array[:, 2]):.2f} ± {np.std(actions_array[:, 2]):.2f}"
            )

    # After demo completes, offer to save agent
    save_choice = input("\nSave agent after demo? (y/n) [n]: ").strip().lower()
    if save_choice == "y":
        filename = input("Enter filename to save agent [agent_demo.pth]: ").strip()
        if not filename:
            filename = "agent_demo.pth"
        agent.save(filename)
        print(f"Agent saved to {filename}")

    return {
        "success_rate": success_rate,
        "avg_trials": avg_trials,
        "total_trials": total_trials,
        "episode_stats": episode_stats,
    }


def compare_agents_demo(
    agents: Dict[str, Any],
    level_name: str = "down_to_earth",
    num_demos: int = 10,
    max_trials: int = 15,
):
    """
    Compare multiple agents in a demo.

    Args:
        agents: Dictionary of agent_name -> agent_instance
        level_name: Level to test on
        num_demos: Number of demonstration episodes per agent
        max_trials: Maximum trials per episode
    """
    print(f"\n{'='*80}")
    print(f"AGENT COMPARISON DEMO")
    print(f"{'='*80}")
    print(f"Level: {level_name}")
    print(f"Episodes per agent: {num_demos}")
    print(f"Max trials per episode: {max_trials}")
    print(f"Agents: {list(agents.keys())}")

    results = {}

    for agent_name, agent in agents.items():
        print(f"\n{'='*60}")
        print(f"Testing {agent_name}...")
        print(f"{'='*60}")

        result = demo_agent(
            agent_name=agent_name,
            agent=agent,
            level_name=level_name,
            num_demos=num_demos,
            max_trials=max_trials,
            show_details=False,  # Less verbose for comparison
        )
        results[agent_name] = result

    # Print comparison summary
    print(f"\n{'='*80}")
    print(f"COMPARISON SUMMARY")
    print(f"{'='*80}")

    # Sort by success rate
    sorted_results = sorted(
        results.items(), key=lambda x: x[1]["success_rate"], reverse=True
    )

    print(
        f"{'Agent':<15} | {'Success Rate':<12} | {'Avg Trials':<10} | {'Total Trials':<12}"
    )
    print("-" * 60)

    for agent_name, stats in sorted_results:
        print(
            f"{agent_name:<15} | {stats['success_rate']:>10.1%} | "
            f"{stats['avg_trials']:>9.1f} | {stats['total_trials']:>11}"
        )

    print("-" * 60)

    # Find best agent
    best_agent, best_stats = sorted_results[0]
    print(
        f"\n🏆 Best performing agent: {best_agent} ({best_stats['success_rate']:.1%} success rate)"
    )

    return results


def interactive_demo(agent_name: str, agent, level_name: str = "down_to_earth"):
    """
    Interactive demo where user can watch agent decisions step by step.

    Args:
        agent_name: Name of the agent
        agent: The agent instance
        level_name: Level to test on
    """
    print(f"\n{'='*60}")
    print(f"INTERACTIVE DEMO: {agent_name.upper()}")
    print(f"{'='*60}")
    print(f"Level: {level_name}")
    print(f"Press Enter to continue each step...")

    # Create environment
    level = load_level(level_name)
    env = PhyreEnv(level=level)

    # Use a random seed
    seed = random.randint(1000, 9999)
    print(f"Using seed: {seed}")

    # Reset environment
    env.reset(seed=seed)
    agent.reset()

    print(f"\nStarting episode...")
    input("Press Enter to see the initial state...")

    # Show initial state
    observation = env._get_observation()
    print(f"Initial observation:")
    print(f"  Objects: {list(observation.get('objects', {}).keys())}")
    print(f"  Step count: {observation.get('step_count', 0)}")

    input("Press Enter for agent to choose action...")

    # Agent chooses action
    action = agent.act(observation)
    print(f"Agent action: [{action[0]:.2f}, {action[1]:.2f}, {action[2]:.2f}]")
    print(f"  X position: {action[0]:.2f}")
    print(f"  Y position: {action[1]:.2f}")
    print(f"  Ball size: {action[2]:.2f}")

    input("Press Enter to run simulation...")

    # Run episode
    success, steps, final_observation = env.run_episode(action)

    if success:
        print(f"✅ SUCCESS! Completed in {steps} steps")
    else:
        print(f"❌ FAILED after {steps} steps")

    print(f"\nDemo complete!")


def main():
    """Main demo function."""
    print("Interphyre Agent Demo")
    print("=" * 50)

    # Create agents for demo
    agents = {
        "Random": RandomAgent(name="random_demo", seed=42),
        "Heuristic": HeuristicAgent(name="heuristic_demo", seed=42),
        "Clean DQN": CleanDQNAgent(
            name="clean_dqn_demo",
            seed=42,
            learning_rate=1e-3,
            gamma=0.99,
            epsilon=0.0,  # No exploration for demo
            hidden_size=128,
        ),
        "PPO": PPOAgent(
            name="ppo_demo", seed=42, learning_rate=3e-4, gamma=0.99, hidden_size=128
        ),
    }

    # Set agents to evaluation mode
    for agent in agents.values():
        if hasattr(agent, "set_training"):
            agent.set_training(False)

    # Demo options
    print("\nDemo Options:")
    print("1. Compare all agents")
    print("2. Demo specific agent")
    print("3. Interactive demo")
    print("4. Demo with pygame visualization")

    choice = input("\nEnter your choice (1-4): ").strip()

    if choice == "1":
        # Compare all agents
        compare_agents_demo(
            agents=agents, level_name="down_to_earth", num_demos=10, max_trials=15
        )

    elif choice == "2":
        # Demo specific agent
        print("\nAvailable agents:")
        for i, agent_name in enumerate(agents.keys(), 1):
            print(f"{i}. {agent_name}")

        agent_choice = input("\nEnter agent number: ").strip()
        try:
            agent_idx = int(agent_choice) - 1
            agent_names = list(agents.keys())
            if 0 <= agent_idx < len(agent_names):
                agent_name = agent_names[agent_idx]
                agent = agents[agent_name]

                demo_agent(
                    agent_name=agent_name,
                    agent=agent,
                    level_name="down_to_earth",
                    num_demos=5,
                    max_trials=15,
                    show_details=True,
                )
            else:
                print("Invalid agent number!")
        except ValueError:
            print("Invalid input!")

    elif choice == "3":
        # Interactive demo
        print("\nAvailable agents:")
        for i, agent_name in enumerate(agents.keys(), 1):
            print(f"{i}. {agent_name}")

        agent_choice = input("\nEnter agent number: ").strip()
        try:
            agent_idx = int(agent_choice) - 1
            agent_names = list(agents.keys())
            if 0 <= agent_idx < len(agent_names):
                agent_name = agent_names[agent_idx]
                agent = agents[agent_name]

                interactive_demo(
                    agent_name=agent_name, agent=agent, level_name="down_to_earth"
                )
            else:
                print("Invalid agent number!")
        except ValueError:
            print("Invalid input!")

    elif choice == "4":
        # Pygame visualization demo
        print("\nAvailable agents:")
        for i, agent_name in enumerate(agents.keys(), 1):
            print(f"{i}. {agent_name}")

        agent_choice = input("\nEnter agent number: ").strip()
        try:
            agent_idx = int(agent_choice) - 1
            agent_names = list(agents.keys())
            if 0 <= agent_idx < len(agent_names):
                agent_name = agent_names[agent_idx]
                agent = agents[agent_name]

                # Get pygame parameters
                fps = input("Enter FPS (default 60): ").strip()
                fps = int(fps) if fps else 60

                pause_time = input(
                    "Enter pause time in seconds (default 1.0): "
                ).strip()
                pause_time = float(pause_time) if pause_time else 1.0

                print(f"\nRunning pygame demo with {agent_name}...")
                print("Press Ctrl+C to stop")

                demo_agent(
                    agent_name=agent_name,
                    agent=agent,
                    level_name="down_to_earth",
                    num_demos=3,  # Fewer demos for pygame
                    max_trials=10,
                    show_details=True,
                    use_pygame=True,
                    fps=fps,
                    pause_time=pause_time,
                )
            else:
                print("Invalid agent number!")
        except ValueError:
            print("Invalid input!")
        except KeyboardInterrupt:
            print("\nDemo stopped by user")

    else:
        print("Invalid choice!")


if __name__ == "__main__":
    main()
