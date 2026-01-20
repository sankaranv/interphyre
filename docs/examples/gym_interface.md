# Gym Interface

Standard Gymnasium (OpenAI Gym) training loop patterns for reinforcement learning research.

## Overview

This example demonstrates:

- Inspecting observation and action spaces
- Sampling random actions
- Running multiple episodes with different seeds
- Tracking episode statistics
- Standard RL training loop structure

**Complexity:** Beginner
**Runtime:** ~5 seconds

## Key Concepts

### Observation Space

A `Box` space representing the initial scene configuration. The observation is a flattened array of object positions, sizes, and properties.

```python
print(env.observation_space)  # Box shape and bounds
```

### Action Space

A `Box` space with shape `(3,)` for `(x, y, radius)`:

```python
env.action_space.sample()  # Returns random (x, y, radius)
```

### Episode Structure

Each episode:

1. `reset()` - Initialize with a new seed
2. `step(action)` - Run full simulation with placed object
3. Check `terminated` and `info['success']`

Note: Unlike most RL environments, `step()` runs the entire physics simulation. Each episode is a single decision.

## Code Example

```python
#!/usr/bin/env python3
"""Gym Interface: Standard RL training loop patterns."""

from interphyre import PhyreEnv

def main():
    # Create environment
    env = PhyreEnv("two_body_problem", seed=42)

    # Inspect spaces
    print(f"Observation space: {env.observation_space}")
    print(f"Action space: {env.action_space}")

    # Track statistics
    successes = 0
    total_reward = 0.0
    num_episodes = 10

    # Standard training loop
    for episode in range(num_episodes):
        # Reset with new seed for variety
        obs, info = env.reset(seed=episode)

        # Sample random action
        action = env.action_space.sample()

        # Step (runs full simulation)
        obs, reward, terminated, truncated, info = env.step(action)

        # Track results
        successes += int(info['success'])
        total_reward += reward

        print(f"Episode {episode + 1}: "
              f"action={tuple(f'{a:.2f}' for a in action)}, "
              f"success={info['success']}, reward={reward:.1f}")

    # Summary
    print(f"\nResults: {successes}/{num_episodes} successes")
    print(f"Average reward: {total_reward / num_episodes:.2f}")

    env.close()
```

## Running the Example

```bash
python demos/02_gym_interface.py
```

## Expected Output

```
==================================================
GYMNASIUM INTERFACE DEMONSTRATION
==================================================

Observation space: Box(-10.0, 10.0, (42,), float32)
Action space: Box([-5. -5.  0.], [5. 5. 1.], (3,), float32)

Running 10 episodes with random actions...

Episode 1:  action=(-1.23, 2.45, 0.67), success=False, reward=0.0
Episode 2:  action=(3.21, -0.89, 0.34), success=False, reward=0.0
...
Episode 10: action=(0.45, 1.23, 0.89), success=False, reward=0.0

==================================================
RESULTS
==================================================
Episodes: 10
Successes: 0 (0.0%)
Average reward: 0.00

Note: Random actions rarely solve levels.
Use learning algorithms to find solutions!
==================================================
```

## Training Tips

### Action Sampling Strategies

```python
# Uniform random (default)
action = env.action_space.sample()

# Biased toward upper region (objects fall down)
action = (
    np.random.uniform(-3, 3),      # x: center-ish
    np.random.uniform(2, 4.5),     # y: upper region
    np.random.uniform(0.3, 0.7)    # radius: medium
)
```

### Multiple Levels

```python
from interphyre.levels import list_levels

for level_name in list_levels():
    env = PhyreEnv(level_name, seed=42)
    # Train on each level...
```

### Deterministic Replay

```python
# Same seed = same initial state
env.reset(seed=42)
env.step((0.5, 3.0, 0.6))  # Always same result for same level
```

## Use Cases

- **RL research:** Train agents to solve physics puzzles
- **Baseline comparisons:** Random agent provides lower bound
- **Curriculum learning:** Progress through easier to harder levels
- **Multi-task learning:** Train on multiple levels simultaneously

## See Also

- [Quickstart](quickstart.md) - Simplest example
- [Triggers](triggers.md) - Event-based control
- [API: Environment](../api/environment.md) - Full reference
