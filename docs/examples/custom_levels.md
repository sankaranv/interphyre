# Custom Levels

Build your own physics puzzles with custom objects and success conditions.

## Overview

This example demonstrates:

- Creating `Level` objects from scratch
- Defining objects (Ball, Bar)
- Setting action objects (user-placeable)
- Writing custom success conditions
- Using `PhyreEnv.from_level()` to run custom levels

**Complexity:** Advanced
**Runtime:** ~2 seconds

## Key Concepts

### Level Structure

A level consists of:

```python
level = Level(
    name="my_level",
    objects={...},           # Dict of physics objects
    action_objects=[...],    # List of user-controllable object names
    success_condition=fn,    # Function(engine) -> bool
    metadata={...}           # Optional description, etc.
)
```

### Object Types

| Type | Description |
|------|-------------|
| `Ball` | Circular physics body |
| `Bar` | Rectangular physics body |
| `Basket` | Container that can hold balls |

### Dynamic vs Static

- `dynamic=True` - Object moves under physics (gravity, collisions)
- `dynamic=False` - Object is fixed in place (platforms, walls)

### Success Conditions

A function that takes the physics engine and returns `True` when the goal is met:

```python
def success_condition(engine):
    # Check if green ball touches blue ball for required duration
    return engine.is_in_contact_for_duration("green", "blue", duration)
```

## Object Reference

### Ball

```python
from interphyre.objects import Ball

Ball(
    x=0.0,          # X position
    y=2.0,          # Y position
    radius=0.5,     # Ball radius
    color="green",  # Visual color
    dynamic=True    # Moves under physics
)
```

### Bar

```python
from interphyre.objects import Bar

Bar(
    x=0.0,          # Center X position
    y=1.0,          # Center Y position
    length=4.0,     # Length of bar
    thickness=0.2,  # Thickness of bar
    angle=-20,      # Rotation in degrees
    dynamic=False   # Static platform
)
```

## Code Example

### Simple Contact Level

```python
from interphyre import PhyreEnv
from interphyre.level import Level
from interphyre.objects import Ball, Bar


def simple_contact_level():
    """Green ball must touch blue ball."""

    objects = {
        "green_ball": Ball(x=-3.0, y=2.0, radius=0.5, color="green", dynamic=True),
        "blue_ball": Ball(x=3.0, y=2.0, radius=0.5, color="blue", dynamic=True),
        "red_ball": Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True),
    }

    def success_condition(engine):
        success_time = engine.config.default_success_time
        return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)

    level = Level(
        name="simple_contact",
        objects=objects,
        action_objects=["red_ball"],  # User controls red ball placement
        success_condition=success_condition,
        metadata={"description": "Make green ball touch blue ball"},
    )

    # Run the level
    env = PhyreEnv.from_level(level)
    env.reset()

    obs, reward, term, trunc, info = env.step((-1.0, 3.0, 0.5))
    print(f"Success: {info['success']}")

    env.close()
```

### Ramp Level

```python
def ramp_level():
    """Roll a ball down a ramp to hit a target."""

    objects = {
        "ball": Ball(x=-3.0, y=3.0, radius=0.3, color="green", dynamic=True),
        "ramp": Bar(x=-1.5, y=1.5, length=4.0, thickness=0.2, angle=-20, dynamic=False),
        "target": Ball(x=2.0, y=-2.0, radius=0.4, color="blue", dynamic=False),
        "action_ball": Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True),
    }

    def success_condition(engine):
        return engine.contact_listener.has_contact("ball", "target")

    level = Level(
        name="ramp_puzzle",
        objects=objects,
        action_objects=["action_ball"],
        success_condition=success_condition,
        metadata={"description": "Roll the ball down the ramp to hit the target"},
    )

    env = PhyreEnv.from_level(level)
    env.reset()
    obs, reward, term, trunc, info = env.step((-3.0, 4.0, 0.5))
    print(f"Success: {info['success']}")
    env.close()
```

### Complex Success Condition

```python
def custom_success_level():
    """Both balls must be below y=0 AND touching."""

    objects = {
        "ball_a": Ball(x=-2.0, y=3.0, radius=0.4, color="green", dynamic=True),
        "ball_b": Ball(x=2.0, y=3.0, radius=0.4, color="blue", dynamic=True),
        "pusher": Ball(x=0.0, y=5.0, radius=0.5, color="red", dynamic=True),
    }

    def success_condition(engine):
        a_body = engine.bodies.get("ball_a")
        b_body = engine.bodies.get("ball_b")

        if not a_body or not b_body:
            return False

        # Check positions
        both_low = a_body.position.y < 0 and b_body.position.y < 0

        # Check contact
        in_contact = engine.contact_listener.has_contact("ball_a", "ball_b")

        return both_low and in_contact

    level = Level(
        name="double_condition",
        objects=objects,
        action_objects=["pusher"],
        success_condition=success_condition,
        metadata={"description": "Both balls must be below y=0 AND touching"},
    )

    env = PhyreEnv.from_level(level)
    env.reset()
    obs, reward, term, trunc, info = env.step((0.0, 4.0, 0.5))
    print(f"Success: {info['success']}")
    env.close()
```

## Running the Example

```bash
python demos/07_custom_levels.py
```

## Expected Output

```
==================================================
CUSTOM LEVELS DEMONSTRATION
==================================================

1. SIMPLE CONTACT LEVEL
----------------------------------------
   Level: simple_contact
   Objects: ['green_ball', 'blue_ball', 'red_ball']
   Action: (-1.0, 3.0, 0.5)
   Success: False

2. RAMP LEVEL
----------------------------------------
   Level: ramp_puzzle
   Success: False

3. PLATFORM LEVEL
----------------------------------------
   Level: platformer
   Platforms: platform1, platform2, platform3
   Success: False

4. CUSTOM SUCCESS CONDITION
----------------------------------------
   Level: double_condition
   Condition: balls below y=0 AND touching
   Success: False

==================================================
Custom level creation demonstrated!

Key components:
  - objects: dict of Ball, Bar, Basket objects
  - action_objects: list of user-placeable object names
  - success_condition: function(engine) -> bool
  - PhyreEnv.from_level(level) to run
==================================================
```

## Success Condition Helpers

The engine provides useful methods for success conditions:

```python
def success_condition(engine):
    # Contact checks
    engine.contact_listener.has_contact("a", "b")  # Current contact
    engine.is_in_contact_for_duration("a", "b", 1.0)  # Sustained contact

    # Object access
    body = engine.bodies["object_name"]
    pos = body.position  # Vec2(x, y)
    vel = body.linearVelocity  # Vec2(x, y)

    # Configuration
    time = engine.config.default_success_time  # Required contact duration
```

## Use Cases

- **Research:** Create specific scenarios for testing
- **Education:** Design puzzles to teach physics concepts
- **Testing:** Unit test specific physics interactions
- **Prototyping:** Quickly iterate on level designs

## See Also

- [API: Level](../api/level.md) - Level model reference
- [API: Objects](../api/objects.md) - Object types reference
- [Levels Gallery](../levels.md) - Built-in levels for inspiration
