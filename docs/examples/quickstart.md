# Quickstart

The simplest possible Interphyre example - create an environment, run a simulation, and check the result.

## Overview

This example demonstrates:

- Creating a `PhyreEnv` with a level name and seed
- Resetting the environment
- Taking an action (placing an object)
- Checking if the level was solved

**Complexity:** Beginner
**Runtime:** ~1 second

## Key Concepts

### PhyreEnv

The main entry point for Interphyre. Wraps the physics simulation in a Gymnasium-compatible interface.

```python
env = PhyreEnv("level_name", seed=42)
```

### Actions

Actions are 3-tuples `(x, y, radius)` specifying where to place the red action ball:

- `x`: Horizontal position (-5.0 to 5.0)
- `y`: Vertical position (-5.0 to 5.0)
- `radius`: Ball size (0.1 to 1.0)

### Success

Check `info['success']` after stepping to see if the level's goal condition was met.

## Code Example

```python
#!/usr/bin/env python3
"""Quickstart: Run a physics puzzle in under 20 lines."""

from interphyre import PhyreEnv

# Create environment for a specific level
env = PhyreEnv("two_body_problem", seed=42)

# Reset to initial state
obs, info = env.reset()

# Take an action: place red ball at (x=0.5, y=3.0) with radius=0.6
action = (0.5, 3.0, 0.6)
obs, reward, terminated, truncated, info = env.step(action)

# Check result
print(f"Level: two_body_problem")
print(f"Action: {action}")
print(f"Success: {info['success']}")
print(f"Reward: {reward}")
print(f"Steps: {info['steps']}")

env.close()
```

## Running the Example

```bash
python demos/01_quickstart.py
```

## Expected Output

```
==================================================
INTERPHYRE QUICKSTART
==================================================

Level: two_body_problem
Action: (0.5, 3.0, 0.6)
Success: False
Reward: 0.0
Steps: 240

Simulation complete!
To solve puzzles, find the right action (x, y, radius).

==================================================
```

## Understanding the Output

- **Success: False** - The action didn't solve the puzzle. Finding solutions requires exploration!
- **Reward: 0.0** - Binary reward (1.0 on success, 0.0 otherwise)
- **Steps: 240** - The simulation ran for 240 physics steps (about 4 seconds of simulated time)

## Next Steps

- Try different actions to solve the level
- Use the [viewer tool](../tools/viewer.md) to visualize what's happening
- Move on to [Gym Interface](gym_interface.md) for RL training patterns

## See Also

- [Gym Interface](gym_interface.md) - Standard RL training loop
- [API: Environment](../api/environment.md) - Full PhyreEnv reference
- [Levels Gallery](../levels.md) - Available puzzle levels
