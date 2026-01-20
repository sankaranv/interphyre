# Getting Started

Interphyre is a Gymnasium-compatible environment for physics-based puzzles. This guide covers installation and basic usage.

## Installation

```bash
pip install interphyre
```

Or from source:

```bash
git clone https://github.com/yourorg/interphyre
cd interphyre
pip install -e .
```

## Quick Start

### Minimal Example

```python
from interphyre import PhyreEnv

# Create environment
env = PhyreEnv("two_body_problem", seed=42)

# Reset and take an action
obs, info = env.reset()
obs, reward, terminated, truncated, info = env.step((0.5, 3.0, 0.6))

print(f"Success: {info['success']}")
env.close()
```

### With Rendering

```python
env = PhyreEnv("catapult", seed=42, render_mode="human")
obs, info = env.reset()
obs, reward, terminated, truncated, info = env.step((0.5, 3.0, 0.6))
env.close()
```

### Standard RL Loop

```python
from interphyre import PhyreEnv

env = PhyreEnv("two_body_problem", seed=42)

for episode in range(10):
    obs, info = env.reset(seed=episode)
    action = env.action_space.sample()  # Random action
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"Episode {episode + 1}: success={info['success']}")

env.close()
```

## Key Concepts

### Actions

Actions are `(x, y, radius)` tuples specifying where to place the red action ball:

- `x`: Horizontal position (-5.0 to 5.0)
- `y`: Vertical position (-5.0 to 5.0)
- `radius`: Ball size (0.1 to 1.5)

### One-Shot Environment

Interphyre is a **one-shot** environment: calling `step()` runs the full physics simulation to completion. Each episode is a single decision - place the action object, then observe the outcome.

### Success Condition

Each level has a success condition (e.g., "green ball touches blue ball for 1 second"). Check `info['success']` after `step()`.

## Intervention API

For multi-turn control (replanning, counterfactuals), enable interventions:

```python
from interphyre import PhyreEnv
from interphyre.interventions import on_contact, on_success

env = PhyreEnv("two_body_problem", seed=42, enable_interventions=True)

# Run until contact event
snapshot, step = env.run_until(
    on_contact("green_ball", "blue_ball"),
    action=(0.5, 3.0, 0.6),
    max_steps=500
)

if snapshot:
    print(f"Contact at step {step}")
    env.restore(snapshot)
    env.apply_impulse("green_ball", impulse=(5.0, 0.0))
    obs, reward, term, trunc, info = env.step_until(on_success())

env.close()
```

## Available Levels

List available levels:

```python
from interphyre.levels import list_levels

print(list_levels())
# ['basket_case', 'catapult', 'two_body_problem', ...]
```

## Running Demos

The `demos/` directory contains progressive examples:

```bash
# Simplest example
python demos/01_quickstart.py

# Run all demos
for f in demos/0*.py; do python $f; done
```

## Viewing Solutions

Use the viewer tool to visualize levels and solutions:

```bash
# View a level with random agent
python tools/viewer.py --level catapult --seed 42

# Play back known solutions
python tools/viewer.py --mode solutions --solutions tests/solutions/successes.json
```

## Next Steps

- **[Examples](examples/index.md)** - Progressive code examples
- **[API Reference](api/index.md)** - Full API documentation
- **[Levels Gallery](levels.md)** - Available puzzle levels
