# Interventions

Mid-simulation modifications — set object attributes, apply forces, add and remove objects.

## Overview

This example demonstrates:

- Setting structural and kinematic attributes with `env.set()`
- Applying impulses and forces
- Adding and removing objects
- Combining interventions inside a `env.branch()` scope

## Intervention Methods

| Method | Description |
|--------|-------------|
| `env.set(name, **attrs)` | Set any attribute on an existing object |
| `env.add(name, obj, impulse=None)` | Add a new physics object |
| `env.remove(name)` | Remove an object |
| `env.impulse(name, impulse, point=None)` | Instantaneous velocity change |
| `env.force(name, force, point=None)` | Continuous force (per step) |
| `env.branch(snapshot)` | Non-destructive counterfactual scope |

## Basic set()

### Structural attributes

Attributes like `radius`, `x`, `y`, `length`, `friction`, and `restitution` trigger body recreation:

```python
env.set("red_ball", radius=0.4)
env.set("red_ball", radius=0.4, restitution=0.9)
env.set("red_ball", x=2.0, y=3.0)
```

### Kinematic attributes

`velocity` and `angular_velocity` are applied directly to the body without recreation:

```python
env.set("green_ball", velocity=(5.0, -3.0))

# Freeze: zero all motion
env.set("green_ball", velocity=(0.0, 0.0), angular_velocity=0.0)
```

## add() and remove()

```python
from interphyre.objects import Ball

env.add("extra_ball", Ball(x=0, y=3, radius=0.3, color="blue", dynamic=True))

# With initial impulse
env.add("fast_ball", Ball(x=-2, y=2, radius=0.4, color="red", dynamic=True), impulse=(5.0, 0.0))

env.remove("black_ball")
```

## impulse() and force()

```python
# Instantaneous impulse
env.impulse("green_ball", (10.0, 5.0))

# Continuous force (per physics step)
env.force("green_ball", (2.0, 0.0))
```

## branch()

Use `env.branch(snapshot)` for non-destructive counterfactual scopes. The simulation is restored to `snapshot` when the block exits.

### Single counterfactual

```python
snapshot, step = env.run_until(on_contact("green_ball", "blue_ball"), action=action)

with env.branch(snapshot):
    env.set("red_ball", radius=0.4)
    env.step_physics(200)
    result = env.success
# world is back at snapshot
```

### Multiple counterfactuals

```python
results = {}
for r in [0.2, 0.4, 0.6]:
    with env.branch(snapshot):
        env.set("red_ball", radius=r)
        env.step_physics(200)
        results[r] = env.success
```

### Combined interventions in one branch

```python
with env.branch(snapshot):
    env.add("helper", Ball(x=-3.0, y=3.0, radius=0.5, color="blue", dynamic=True))
    env.impulse("helper", (8.0, 0.0))
    env.set("green_ball", velocity=(0.0, 0.0), angular_velocity=0.0)
    env.step_physics(200)
    result = env.success
```

## Running the Example

```bash
python demos/interventions.py
```
