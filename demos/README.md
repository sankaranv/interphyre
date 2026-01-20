# Interphyre Demos

Progressive examples demonstrating interphyre's capabilities.

## Demo Overview

| Demo | Purpose |
|------|---------|
| `01_quickstart.py` | Simplest usage - create env, step, check result |
| `02_gym_interface.py` | Standard RL training loop with Gymnasium |
| `03_triggers.py` | All trigger types (time, contact, velocity, etc.) |
| `04_interventions.py` | Mid-simulation modifications (add objects, apply forces) |
| `05_replanning.py` | Multi-turn workflow: run_until, restore, continue |
| `06_counterfactuals.py` | Causal analysis with branching simulations |
| `07_custom_levels.py` | Building custom levels from scratch |

## Quick Start

```bash
# Simplest example
python demos/01_quickstart.py

# Run all demos
for f in demos/0*.py; do python $f; done
```

## Detailed Descriptions

### 01_quickstart.py
The absolute minimum code to run a simulation. Shows how to:
- Create an environment with `PhyreEnv("level_name", seed=42)`
- Reset and step
- Check success/failure

### 02_gym_interface.py
Standard RL training loop pattern. Shows how to:
- Inspect observation and action spaces
- Sample random actions
- Run multiple episodes
- Track statistics

### 03_triggers.py
Event detection in physics simulations. Demonstrates:
- `at_step(n)` - time-based
- `on_contact("a", "b")` - specific pair contact
- `on_contact_with("a")` - any contact with object
- `on_success()` - level success condition
- `on_velocity_threshold()` - physics-based
- `on_position_threshold()` - position-based
- `when(lambda)` - custom condition
- `on_sequence([...])` - sequential patterns

### 04_interventions.py
Mid-simulation object modifications. Shows how to:
- `add_object()` - add new objects
- `apply_impulse()` / `apply_force()` - apply physics
- `set_velocity()` / `set_position()` - direct state changes
- `freeze()` - stop objects
- `intervention_context()` - batch multiple changes

### 05_replanning.py
The core multi-turn agent workflow. Demonstrates:
- `run_until(trigger, action=...)` - run until event
- `restore(snapshot)` - return to checkpoint
- `step_until(trigger)` - continue simulation
- The observe-decide-act loop

### 06_counterfactuals.py
Causal inference with branching. Shows how to:
- Capture state at a branch point
- Run factual branch (no intervention)
- Run counterfactual branch (with intervention)
- Compare outcomes and measure causal effect

### 07_custom_levels.py
Building custom physics puzzles. Demonstrates:
- Creating `Level` objects with objects, action_objects, success_condition
- Using `Ball`, `Bar`, and other object types
- Writing custom success conditions
- Using `PhyreEnv.from_level(level)` to run custom levels

## Tools

For interactive visualization and video recording, see:
- `tools/viewer.py` - Solution viewer and level explorer
- `tools/video_recorder.py` - Video recording utility

```bash
# View a level with random agent
python tools/viewer.py --level catapult --seed 42

# View known solutions
python tools/viewer.py --mode solutions --solutions tests/solutions/successes.json

# Record video
python tools/viewer.py --level catapult --seed 42 --record-video --video-format gif
```
