# Examples

Progressive examples demonstrating Interphyre's capabilities for physics simulation, reinforcement learning, and causal inference research.

## Quick Start

```bash
# Run the simplest example
python demos/01_quickstart.py

# Run all demos in order
for f in demos/0*.py; do python $f; done
```

## Demo Overview

| Demo | Purpose | Complexity |
|------|---------|------------|
| [01 Quickstart](quickstart.md) | Simplest usage - create env, step, check result | Beginner |
| [02 Gym Interface](gym_interface.md) | Standard RL training loop with Gymnasium | Beginner |
| [03 Triggers](triggers.md) | All trigger types (time, contact, velocity, etc.) | Intermediate |
| [04 Interventions](interventions.md) | Mid-simulation modifications (add objects, apply forces) | Intermediate |
| [05 Replanning](replanning.md) | Multi-turn workflow: run_until, restore, continue | Intermediate |
| [06 Counterfactuals](counterfactuals.md) | Causal analysis with branching simulations | Advanced |
| [07 Custom Levels](custom_levels.md) | Building custom levels from scratch | Advanced |

## Learning Paths

### New to Interphyre?

Follow the demos in order:

1. **[Quickstart](quickstart.md)** - Understand the basic API
2. **[Gym Interface](gym_interface.md)** - Standard RL patterns
3. **[Triggers](triggers.md)** - Event detection
4. **[Interventions](interventions.md)** - Modifying simulations
5. **[Replanning](replanning.md)** - Multi-turn control
6. **[Counterfactuals](counterfactuals.md)** - Causal analysis
7. **[Custom Levels](custom_levels.md)** - Creating your own puzzles

### For RL Researchers

Focus on these demos:

1. **[Gym Interface](gym_interface.md)** - Training loop patterns
2. **[Quickstart](quickstart.md)** - Minimal environment usage
3. **[Custom Levels](custom_levels.md)** - Create training scenarios

Key API: `InterphyreEnv`, `observation_space`, `action_space`, `step()`, `reset()`

### For Causal Inference

Focus on these demos:

1. **[Counterfactuals](counterfactuals.md)** - Branching and comparison
2. **[Triggers](triggers.md)** - Define branch points
3. **[Interventions](interventions.md)** - Apply causal interventions
4. **[Replanning](replanning.md)** - Multi-turn analysis

Key API: `run_until()`, `restore()`, `intervention_context()`, triggers

### For Replanning Agents

Focus on these demos:

1. **[Replanning](replanning.md)** - Core multi-turn workflow
2. **[Triggers](triggers.md)** - Event-based checkpoints
3. **[Interventions](interventions.md)** - Actions at checkpoints
4. **[Counterfactuals](counterfactuals.md)** - Strategy comparison

Key API: `run_until()`, `step_until()`, `restore()`, triggers

## Tools

For interactive visualization and debugging, see the tools directory:

### Solution Viewer

Visualize levels and play back solutions:

```bash
# View a level with random agent
python tools/viewer.py --level catapult --seed 42

# View known solutions
python tools/viewer.py --mode solutions --solutions tests/solutions/successes.json

# Record video
python tools/viewer.py --level catapult --seed 42 --record-video --video-format gif
```

### Video Recorder

Record simulation videos programmatically:

```bash
python tools/video_recorder.py --level two_body_problem --action "0.5,3.0,0.6" --output demo.mp4
```

## API Reference

For detailed API documentation, see:

- **[InterphyreEnv](../api/environment.md)** - Main environment class
- **[Interventions](../api/interventions.md)** - Triggers and modifications
- **[Objects](../api/objects.md)** - Ball, Bar, Basket classes
- **[Level](../api/level.md)** - Level model and creation
