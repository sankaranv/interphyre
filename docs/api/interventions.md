# Interventions

The interventions module provides tools for multi-turn simulation control, including triggers, state snapshots, and mid-simulation modifications.

## Quick Start

```python
from interphyre import InterphyreEnv
from interphyre.interventions import on_contact, at_step, on_success

env = InterphyreEnv("two_body_problem", seed=42)

# Run until contact event
snapshot, step = env.run_until(
    on_contact("green_ball", "blue_ball"),
    action=[(0.5, 3.0, 0.5)],
    max_steps=500
)

if snapshot:
    with env.branch(snapshot):
        env.impulse("green_ball", (5.0, 0.0))
        env.step_physics(200)
        success = env.success
```

## Modification Methods

All modification methods are called directly on `InterphyreEnv`.

### env.set(name, \*\*attrs)

Set one or more attributes on an existing object. Kinematic attributes (`velocity`, `angular_velocity`) are applied directly to the Box2D body. The `color` attribute is set via setattr only. All other attributes (e.g. `radius`, `length`, `x`, `y`, `friction`, `restitution`) trigger body recreation.

```python
# Set structural property
env.set("red_ball", radius=0.4)
env.set("red_ball", radius=0.4, restitution=0.9)

# Set position
env.set("red_ball", x=2.0, y=3.0)

# Set velocity
env.set("red_ball", velocity=(5.0, 0.0))

# Freeze (zero all motion)
env.set("red_ball", velocity=(0.0, 0.0), angular_velocity=0.0)
```

#### Attribute dispatch

| Attribute | Dispatch |
|-----------|----------|
| `velocity` | Applied directly to body |
| `angular_velocity` | Applied directly to body |
| `color` | setattr only (no physics change) |
| everything else (`radius`, `x`, `y`, `length`, `friction`, `restitution`, …) | Body recreation |

### env.add(name, obj, impulse=None)

Add a new physics object to the simulation. Optionally apply an impulse immediately after creation.

```python
from interphyre.objects import Ball

env.add("extra_ball", Ball(x=0, y=3, radius=0.3, color="blue", dynamic=True))
env.add("fast_ball", Ball(x=-2, y=2, radius=0.4, color="red", dynamic=True), impulse=(5.0, 0.0))
```

### env.remove(name)

Remove an object from the simulation.

```python
env.remove("black_ball")
```

### env.impulse(name, impulse, point=None)

Apply an instantaneous impulse to an object. `impulse` is a `(fx, fy)` tuple in world units. `point` is an optional world-space application point; defaults to the body's center of mass.

```python
env.impulse("green_ball", (10.0, 5.0))
env.impulse("green_ball", (10.0, 5.0), point=(0.1, 0.0))
```

### env.force(name, force, point=None)

Apply a continuous force (per physics step). `force` is a `(fx, fy)` tuple. Persists until cleared or the body is removed.

```python
env.force("green_ball", (2.0, 0.0))
```

### env.branch(snapshot)

Return a context manager that restores the simulation to `snapshot` on both entry and exit. Use this for non-destructive counterfactual branches: the world is in the snapshot state inside the block and is restored when the block exits, regardless of what happened inside.

```python
# Single counterfactual
with env.branch(snapshot):
    env.set("red_ball", radius=0.4)
    env.step_physics(200)
    result = env.success
# world is back at snapshot here

# Multiple counterfactuals from the same snapshot
results = {}
for r in [0.2, 0.4, 0.6]:
    with env.branch(snapshot):
        env.set("red_ball", radius=r)
        env.step_physics(200)
        results[r] = env.success
```

## Triggers

Triggers define WHEN something should happen during simulation. Use them with `env.run_until()` and `env.step_until()`.

### at_step(n)

Fire at a specific simulation step.

```python
from interphyre.interventions import at_step

snapshot, step = env.run_until(at_step(100), action=action)
# step == 100
```

### on_contact(obj_a, obj_b)

Fire when two specific objects touch.

```python
from interphyre.interventions import on_contact

snapshot, step = env.run_until(
    on_contact("green_ball", "blue_ball"),
    action=action
)
```

### on_contact_with(obj)

Fire when an object touches anything.

```python
from interphyre.interventions import on_contact_with

snapshot, step = env.run_until(on_contact_with("green_ball"), action=action)
```

### on_success()

Fire when the level's success condition is met.

```python
from interphyre.interventions import on_success

snapshot, step = env.run_until(on_success(), action=action, max_steps=500)
if snapshot:
    print(f"Level solved at step {step}!")
```

### on_velocity_threshold(obj, speed, above=True)

Fire when object exceeds (or drops below) a speed threshold.

```python
from interphyre.interventions import on_velocity_threshold

# Fire when green_ball goes faster than 3.0 units/second
trigger = on_velocity_threshold("green_ball", speed_threshold=3.0, above=True)
```

### on_position_threshold(obj, axis, threshold, direction)

Fire when object crosses a position threshold.

```python
from interphyre.interventions import on_position_threshold

# Fire when green_ball's y position goes below -2.0
trigger = on_position_threshold(
    "green_ball",
    axis="y",
    threshold=-2.0,
    direction="below"  # or "above"
)
```

### when(condition)

Fire when a custom condition function returns True.

```python
from interphyre.interventions import when

def both_balls_low(engine):
    green_y = engine.bodies["green_ball"].position.y
    blue_y = engine.bodies["blue_ball"].position.y
    return green_y < 0 and blue_y < 0

snapshot, step = env.run_until(when(both_balls_low), action=action)
```

### on_sequence(triggers)

Fire when multiple triggers fire in order.

```python
from interphyre.interventions import on_sequence, on_contact

# First red hits green, then green hits blue
trigger = on_sequence([
    on_contact("red_ball", "green_ball"),
    on_contact("green_ball", "blue_ball"),
])
```

### on_any(triggers)

Fire when any trigger fires.

```python
from interphyre.interventions import on_any, on_contact, at_step

# Fire on contact OR at step 200, whichever comes first
trigger = on_any([
    on_contact("green_ball", "blue_ball"),
    at_step(200),
])
```

## StateSnapshot

Captures complete simulation state for later restoration.

```python
from interphyre.interventions import StateSnapshot

# Capture via run_until (recommended)
snapshot, step = env.run_until(at_step(50), action=action)

# Restore (raw primitive — prefer env.branch() for counterfactuals)
env.restore(snapshot)

# Low-level capture (when needed)
snapshot = StateSnapshot.capture(env.engine, metadata={"note": "custom"})
snapshot.restore(env.engine)
```

### Snapshot Contents

- All body positions, velocities, angles
- Contact listener state
- Current simulation time
- Optional metadata

## Trigger Classes

For advanced use cases, you can work with trigger classes directly:

| Class | Factory Function | Description |
|-------|-----------------|-------------|
| `TimeBasedTrigger` | `at_step(n)` | Fire at step n |
| `EventBasedTrigger` | `on_contact()`, `on_contact_with()`, `on_success()` | Fire on physics events |
| `ConditionBasedTrigger` | `when(fn)` | Fire when condition is true |
| `SequenceTrigger` | `on_sequence([...])` | Fire when sequence completes |
| `AnyTrigger` | `on_any([...])` | Fire when any sub-trigger fires |

### Trigger Interface

All triggers implement:

```python
class Trigger:
    def should_fire(self, step: int, engine: Box2DEngine) -> bool:
        """Check if trigger should fire at this step."""
        ...

    def reset(self) -> None:
        """Reset trigger state (for reuse)."""
        ...
```

## Import Summary

Most users need only:

```python
from interphyre.interventions import (
    # Triggers
    at_step,
    on_contact,
    on_contact_with,
    on_success,
    on_velocity_threshold,
    on_position_threshold,
    when,
    on_sequence,
    on_any,
)
```

The `InterphyreEnv` class provides `run_until()`, `restore()`, `branch()`, `step_until()`, and `step_physics()` methods that handle most intervention workflows.

## See Also

- [Environment](environment.md) - InterphyreEnv intervention methods
- [Examples: Triggers](../examples/triggers.md) - Trigger examples
- [Examples: Interventions](../examples/interventions.md) - Modification examples
- [Examples: Replanning](../examples/replanning.md) - Multi-turn workflows
- [Examples: Counterfactuals](../examples/counterfactuals.md) - Causal analysis
