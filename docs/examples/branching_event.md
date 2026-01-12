# Branching Event Example

Event-driven branching demonstration showing how to pause simulation at trigger points and create factual vs. counterfactual trajectories.

## Overview

This example demonstrates:

- Running simulation until a trigger fires
- Capturing snapshot at event
- Branching into factual and counterfactual trajectories
- Adding objects mid-simulation
- Comparing outcomes

**Complexity:** Beginner
**Runtime:** ~1-2 seconds

## Key Concepts

### StateSnapshot
Captures complete simulation state including all object positions, velocities, and physics state.

### Triggers
Event detectors that fire when specific conditions are met (e.g., object contact, velocity threshold).

### SimulationTrajectory
Manages diverging simulation paths from a common snapshot.

## Code Example

```python
from interphyre import Box2DEngine
from interphyre.config import SimulationConfig
from interphyre.interventions import (
    StateSnapshot,
    SimulationTrajectory,
    on_contact,
    CallableIntervention,
)
from interphyre.levels import load_level

# Load level with interventions enabled
level = load_level("two_body_problem")
config = SimulationConfig(enable_interventions=True)
engine = Box2DEngine(level, config)

# Run until contact event
trigger = on_contact("green_ball", "blue_ball", once_only=True)
snapshot = None

for step in range(240):
    engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
    engine.time_update(config.time_step)

    if trigger.should_fire(step + 1, engine):
        snapshot = StateSnapshot.capture(engine)
        break

if snapshot:
    # Factual branch (no intervention)
    factual = SimulationTrajectory(snapshot=snapshot)
    factual.execute(engine, steps=120)
    factual_success = engine.level.success_condition(engine)

    # Counterfactual branch (add red ball)
    def spawn_red_ball(engine):
        engine.place_action_objects([(2.0, 3.0, 0.5)])

    counterfactual = SimulationTrajectory(snapshot=snapshot)
    counterfactual.apply_intervention(CallableIntervention(spawn_red_ball))
    counterfactual.execute(engine, steps=120)
    counterfactual_success = engine.level.success_condition(engine)

    print(f"Factual: {factual_success}")
    print(f"Counterfactual: {counterfactual_success}")
```

## Running the Example

```bash
python demos/branching_event.py
```

## Expected Output

```
=== Event-Driven Branching Demo ===
Contact detected at step 45
Factual result: FAILURE
Counterfactual result: SUCCESS
Causal effect: +1.0
```

## Use Cases

- **Basic causal inference:** Compare outcomes with and without intervention
- **Understanding intervention API:** Learn core concepts of snapshots and trajectories
- **Single-event branching:** Simple pause-and-branch pattern

## See Also

- [Velocity Trigger](velocity_trigger.md) - Different trigger type
- [Sequence Detection](sequence_detection.md) - Multiple events in sequence
- [API: Interventions](../api/interventions.md) - Full API reference
