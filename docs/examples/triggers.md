# Triggers

Event detection in physics simulations - fire callbacks or pause execution when specific conditions are met.

## Overview

This example demonstrates all trigger types:

- **Time-based:** `at_step(n)` - fire at specific step
- **Contact-based:** `on_contact()`, `on_contact_with()` - object collisions
- **Success-based:** `on_success()` - level goal achieved
- **Physics-based:** `on_velocity_threshold()`, `on_position_threshold()` - state thresholds
- **Custom:** `when(lambda)` - arbitrary conditions
- **Sequential:** `on_sequence([...])` - events in order

**Complexity:** Intermediate
**Runtime:** ~3 seconds

## Key Concepts

### Triggers and run_until()

Triggers define WHEN something should happen. Use with `run_until()`:

```python
snapshot, step = env.run_until(trigger, action=(...), max_steps=500)
if snapshot:
    print(f"Trigger fired at step {step}")
```

### Snapshot

When a trigger fires, `run_until()` returns a `StateSnapshot` capturing the complete simulation state at that moment. Use `env.restore(snapshot)` to return to that point.

## Trigger Reference

### at_step(n)

Fire at a specific simulation step.

```python
from interphyre.interventions import at_step

trigger = at_step(100)
snapshot, step = env.run_until(trigger, action=(0.5, 3.0, 0.5), max_steps=200)
# step == 100
```

### on_contact(obj_a, obj_b)

Fire when two specific objects touch.

```python
from interphyre.interventions import on_contact

trigger = on_contact("green_ball", "blue_ball")
snapshot, step = env.run_until(trigger, action=(-4.5, 4.5, 0.5), max_steps=500)
```

### on_contact_with(obj)

Fire when an object touches anything.

```python
from interphyre.interventions import on_contact_with

trigger = on_contact_with("green_ball")
snapshot, step = env.run_until(trigger, action=(0.5, 3.0, 0.5), max_steps=300)
```

### on_success()

Fire when the level's success condition is met.

```python
from interphyre.interventions import on_success

trigger = on_success()
snapshot, step = env.run_until(trigger, action=(0.76, 4.27, 0.58), max_steps=500)
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
    direction="below"
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

trigger = when(both_balls_low)
```

### on_sequence([triggers])

Fire when multiple triggers fire in order.

```python
from interphyre.interventions import on_sequence, on_contact

# First red hits green, then green hits blue
sequence = on_sequence([
    on_contact("red_ball", "green_ball"),
    on_contact("green_ball", "blue_ball"),
])
snapshot, step = env.run_until(sequence, action=(-4.5, 4.5, 0.5), max_steps=500)
```

## Code Example

```python
#!/usr/bin/env python3
"""Triggers: Event detection in physics simulations."""

from interphyre import PhyreEnv
from interphyre.interventions import (
    at_step,
    on_contact,
    on_contact_with,
    on_position_threshold,
    on_sequence,
    on_success,
    on_velocity_threshold,
    when,
)

def demo_time_trigger():
    """Time-based trigger: fires at a specific step."""
    env = PhyreEnv("two_body_problem", seed=42, enable_interventions=True)

    trigger = at_step(100)
    snapshot, step = env.run_until(trigger, action=(0.5, 3.0, 0.5), max_steps=200)

    print(f"at_step(100): fired at step {step}")
    env.close()

def demo_contact_trigger():
    """Contact-based trigger: fires when two objects touch."""
    env = PhyreEnv("two_body_problem", seed=0, enable_interventions=True)

    trigger = on_contact("green_ball", "blue_ball")
    snapshot, step = env.run_until(trigger, action=(-4.5, 4.5, 0.5), max_steps=500)

    if snapshot:
        print(f"on_contact(): balls contacted at step {step}")
    else:
        print("on_contact(): balls never contacted")
    env.close()

# ... more trigger demos
```

## Running the Example

```bash
python demos/03_triggers.py
```

## Expected Output

```
==================================================
TRIGGER TYPES DEMONSTRATION
==================================================

1. TIME TRIGGER: at_step(100)
----------------------------------------
   Trigger fired at step 100

2. CONTACT TRIGGER: on_contact('green_ball', 'blue_ball')
----------------------------------------
   Balls contacted at step 343

3. CONTACT-WITH TRIGGER: on_contact_with('green_ball')
----------------------------------------
   green_ball contacted something at step 87

4. SUCCESS TRIGGER: on_success()
----------------------------------------
   Level solved at step 185!

5. VELOCITY TRIGGER: on_velocity_threshold('green_ball', 3.0)
----------------------------------------
   green_ball exceeded 3.0 speed at step 42 (speed=3.45)

6. POSITION TRIGGER: on_position_threshold('green_ball', 'y', -2.0)
----------------------------------------
   green_ball crossed y=-2.0 at step 156 (y=-2.15)

7. CUSTOM TRIGGER: when(lambda)
----------------------------------------
   Both balls below y=0 at step 198

8. SEQUENCE TRIGGER: on_sequence([contact1, contact2])
----------------------------------------
   Sequence completed at step 412
   (red hit green, then green hit blue)

==================================================
All trigger types demonstrated!
==================================================
```

## Use Cases

- **Replanning agents:** Pause at key events to reconsider strategy
- **Causal inference:** Capture state at interesting moments
- **Data collection:** Record when specific physics events occur
- **Debugging:** Inspect simulation at precise moments

## See Also

- [Interventions](interventions.md) - Modify simulation when triggers fire
- [Replanning](replanning.md) - Multi-turn control with triggers
- [Counterfactuals](counterfactuals.md) - Branch at trigger points
- [API: Interventions](../api/interventions.md) - Full reference
