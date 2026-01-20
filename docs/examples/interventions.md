# Interventions

Mid-simulation modifications - add objects, apply forces, and change physics state.

## Overview

This example demonstrates:

- Adding new objects during simulation
- Applying impulses and forces
- Setting velocities and positions directly
- Freezing objects
- Batching multiple changes with `intervention_context()`

**Complexity:** Intermediate
**Runtime:** ~2 seconds

## Key Concepts

### Enabling Interventions

Interventions require `enable_interventions=True`:

```python
env = PhyreEnv("level_name", seed=42, enable_interventions=True)
```

### Intervention Methods

All methods are available directly on `PhyreEnv`:

| Method | Description |
|--------|-------------|
| `add_object(name, obj, impulse=None)` | Add new physics object |
| `apply_impulse(name, impulse)` | Instantaneous velocity change |
| `apply_force(name, force)` | Continuous force |
| `set_velocity(name, vx, vy)` | Set exact velocity |
| `set_position(name, x, y)` | Teleport object |
| `freeze(name)` | Stop all motion |

### InterventionContext

Batch multiple changes atomically:

```python
with env.intervention_context() as ctx:
    ctx.add_object("ball1", Ball(...))
    ctx.apply_impulse("ball1", (5.0, 0.0))
    ctx.freeze("other_ball")
```

## Intervention Reference

### add_object(name, object, impulse=None)

Add a new physics object to the simulation.

```python
from interphyre.objects import Ball

env.add_object(
    "new_ball",
    Ball(x=2.0, y=3.0, radius=0.3, color="blue", dynamic=True)
)

# With initial impulse
env.add_object(
    "fast_ball",
    Ball(x=-2.0, y=2.0, radius=0.4, color="red", dynamic=True),
    impulse=(5.0, 0.0)  # Rightward impulse
)
```

### apply_impulse(name, impulse)

Apply an instantaneous velocity change (impulse).

```python
# Give green_ball a kick to the right and up
env.apply_impulse("green_ball", impulse=(10.0, 5.0))
```

### apply_force(name, force)

Apply a continuous force (per physics step).

```python
# Apply rightward force
env.apply_force("green_ball", force=(2.0, 0.0))
```

### set_velocity(name, vx, vy)

Set exact velocity, replacing current motion.

```python
env.set_velocity("green_ball", vx=5.0, vy=-3.0)
```

### set_position(name, x, y)

Teleport object to new position.

```python
env.set_position("green_ball", x=0.0, y=0.0)
```

### freeze(name)

Stop object completely (zero velocity and angular velocity).

```python
env.freeze("green_ball")
```

### intervention_context()

Group multiple interventions for cleaner code:

```python
with env.intervention_context() as ctx:
    ctx.add_object(
        "helper_ball",
        Ball(x=-3.0, y=3.0, radius=0.5, color="blue", dynamic=True)
    )
    ctx.apply_impulse("helper_ball", impulse=(8.0, 0.0))
    ctx.set_velocity("green_ball", vx=0.0, vy=0.0)
```

## Code Example

```python
#!/usr/bin/env python3
"""Interventions: Modifying simulations mid-flight."""

from interphyre import PhyreEnv
from interphyre.interventions import at_step
from interphyre.objects import Ball


def demo_add_object():
    """Add a new object during simulation."""
    env = PhyreEnv("two_body_problem", seed=42, enable_interventions=True)

    # Run to step 50
    snapshot, _ = env.run_until(at_step(50), action=(0.5, 3.0, 0.5), max_steps=100)
    env.restore(snapshot)

    # Add a new ball
    env.add_object(
        "new_ball",
        Ball(x=2.0, y=3.0, radius=0.3, color="blue", dynamic=True)
    )

    print(f"Added 'new_ball' at (2.0, 3.0)")
    print(f"Objects now: {list(env.level.objects.keys())}")
    env.close()


def demo_apply_impulse():
    """Apply impulse to existing object."""
    env = PhyreEnv("two_body_problem", seed=42, enable_interventions=True)

    snapshot, _ = env.run_until(at_step(50), action=(0.5, 3.0, 0.5), max_steps=100)
    env.restore(snapshot)

    before = env.engine.bodies["green_ball"].linearVelocity
    print(f"Before: velocity=({before.x:.2f}, {before.y:.2f})")

    env.apply_impulse("green_ball", impulse=(10.0, 5.0))

    after = env.engine.bodies["green_ball"].linearVelocity
    print(f"After:  velocity=({after.x:.2f}, {after.y:.2f})")
    env.close()


def demo_intervention_context():
    """Use InterventionContext for multiple changes."""
    env = PhyreEnv("two_body_problem", seed=42, enable_interventions=True)

    snapshot, _ = env.run_until(at_step(50), action=(0.5, 3.0, 0.5), max_steps=100)
    env.restore(snapshot)

    with env.intervention_context() as ctx:
        ctx.add_object(
            "helper_ball",
            Ball(x=-3.0, y=3.0, radius=0.5, color="blue", dynamic=True)
        )
        ctx.apply_impulse("helper_ball", impulse=(8.0, 0.0))
        ctx.set_velocity("green_ball", vx=0.0, vy=0.0)

    print("Applied multiple interventions atomically")
    env.close()
```

## Running the Example

```bash
python demos/04_interventions.py
```

## Expected Output

```
==================================================
INTERVENTION TYPES DEMONSTRATION
==================================================

1. ADD OBJECT
----------------------------------------
   Added 'new_ball' at (2.0, 3.0)
   Objects now: ['green_ball', 'blue_ball', 'red_ball', 'new_ball']

2. ADD OBJECT WITH IMPULSE
----------------------------------------
   Added 'fast_ball' with velocity (5.00, 0.00)

3. APPLY IMPULSE
----------------------------------------
   green_ball velocity before: (0.12, -2.45)
   green_ball velocity after:  (10.12, 2.55)

4. SET VELOCITY
----------------------------------------
   Set green_ball velocity to (5.00, -3.00)

5. SET POSITION
----------------------------------------
   green_ball position before: (-1.23, 1.45)
   green_ball position after:  (0.00, 0.00)

6. FREEZE OBJECT
----------------------------------------
   green_ball velocity before: (0.12, -2.45)
   green_ball velocity after:  (0.00, 0.00)

7. INTERVENTION CONTEXT (batched changes)
----------------------------------------
   Applied multiple interventions:
   - Added helper_ball
   - Applied impulse to helper_ball
   - Stopped green_ball

==================================================
All intervention types demonstrated!
==================================================
```

## Use Cases

- **Replanning agents:** Modify simulation based on observations
- **Causal experiments:** Add/remove objects to test causal effects
- **Debugging:** Manually position objects to test specific scenarios
- **Game mechanics:** Create interactive physics puzzles

## See Also

- [Triggers](triggers.md) - Detect when to intervene
- [Replanning](replanning.md) - Multi-turn control workflow
- [Counterfactuals](counterfactuals.md) - Compare intervention vs no intervention
- [API: Interventions](../api/interventions.md) - Full reference
