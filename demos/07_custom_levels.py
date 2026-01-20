#!/usr/bin/env python3
"""
Custom Levels: Build your own physics puzzles.

This demo shows how to create custom levels from scratch:
1. Define objects (balls, bars, baskets)
2. Set action objects (user-placeable)
3. Write success conditions
4. Use PhyreEnv.from_level() to run

Custom levels are useful for testing specific scenarios or research.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from interphyre import PhyreEnv
from interphyre.level import Level
from interphyre.objects import Ball, Bar


def simple_contact_level():
    """Create a level where green ball must touch blue ball."""
    print("\n1. SIMPLE CONTACT LEVEL")
    print("-" * 40)

    # Define objects
    objects = {
        "green_ball": Ball(x=-3.0, y=2.0, radius=0.5, color="green", dynamic=True),
        "blue_ball": Ball(x=3.0, y=2.0, radius=0.5, color="blue", dynamic=True),
        "red_ball": Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True),
    }

    # Success condition: green touches blue
    def success_condition(engine):
        success_time = engine.config.default_success_time
        return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)

    # Create level
    level = Level(
        name="simple_contact",
        objects=objects,
        action_objects=["red_ball"],  # User controls red ball placement
        success_condition=success_condition,
        metadata={"description": "Make green ball touch blue ball"},
    )

    # Run with the level
    env = PhyreEnv.from_level(level)
    env.reset()

    # Try an action
    obs, reward, term, trunc, info = env.step((-1.0, 3.0, 0.5))
    print(f"   Level: {level.name}")
    print(f"   Objects: {list(objects.keys())}")
    print(f"   Action: (-1.0, 3.0, 0.5)")
    print(f"   Success: {info['success']}")

    env.close()


def ramp_level():
    """Create a level with a ramp to roll balls."""
    print("\n2. RAMP LEVEL")
    print("-" * 40)

    # A ramp made of a tilted bar, ball must roll down and hit target
    objects = {
        "ball": Ball(x=-3.0, y=3.0, radius=0.3, color="green", dynamic=True),
        "ramp": Bar(x=-1.5, y=1.5, length=4.0, thickness=0.2, angle=-20, dynamic=False),
        "target": Ball(x=2.0, y=-2.0, radius=0.4, color="blue", dynamic=False),
        "action_ball": Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True),
    }

    def success_condition(engine):
        # Ball must touch target
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

    # Try dropping action ball on the main ball
    obs, reward, term, trunc, info = env.step((-3.0, 4.0, 0.5))
    print(f"   Level: {level.name}")
    print(f"   Success: {info['success']}")

    env.close()


def platform_level():
    """Create a level with platforms to navigate."""
    print("\n3. PLATFORM LEVEL")
    print("-" * 40)

    objects = {
        "ball": Ball(x=-4.0, y=4.0, radius=0.3, color="green", dynamic=True),
        "platform1": Bar(x=-2.5, y=2.5, length=2.0, thickness=0.2, angle=0, dynamic=False),
        "platform2": Bar(x=0.0, y=1.0, length=2.0, thickness=0.2, angle=0, dynamic=False),
        "platform3": Bar(x=2.5, y=-0.5, length=2.0, thickness=0.2, angle=0, dynamic=False),
        "goal": Ball(x=3.5, y=-3.0, radius=0.5, color="blue", dynamic=False),
        "pusher": Ball(x=0.0, y=5.0, radius=0.6, color="red", dynamic=True),
    }

    def success_condition(engine):
        return engine.contact_listener.has_contact("ball", "goal")

    level = Level(
        name="platformer",
        objects=objects,
        action_objects=["pusher"],
        success_condition=success_condition,
        metadata={"description": "Guide ball across platforms to goal"},
    )

    env = PhyreEnv.from_level(level)
    env.reset()

    obs, reward, term, trunc, info = env.step((-4.0, 4.5, 0.6))
    print(f"   Level: {level.name}")
    print(f"   Platforms: platform1, platform2, platform3")
    print(f"   Success: {info['success']}")

    env.close()


def custom_success_level():
    """Create a level with a complex success condition."""
    print("\n4. CUSTOM SUCCESS CONDITION")
    print("-" * 40)

    objects = {
        "ball_a": Ball(x=-2.0, y=3.0, radius=0.4, color="green", dynamic=True),
        "ball_b": Ball(x=2.0, y=3.0, radius=0.4, color="blue", dynamic=True),
        "pusher": Ball(x=0.0, y=5.0, radius=0.5, color="red", dynamic=True),
    }

    def success_condition(engine):
        # Success: both balls must be below y=0 AND touching
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
        metadata={
            "description": "Both balls must be below y=0 AND touching each other"
        },
    )

    env = PhyreEnv.from_level(level)
    env.reset()

    obs, reward, term, trunc, info = env.step((0.0, 4.0, 0.5))
    print(f"   Level: {level.name}")
    print(f"   Condition: balls below y=0 AND touching")
    print(f"   Success: {info['success']}")

    env.close()


def main():
    print("=" * 50)
    print("CUSTOM LEVELS DEMONSTRATION")
    print("=" * 50)

    simple_contact_level()
    ramp_level()
    platform_level()
    custom_success_level()

    print("\n" + "=" * 50)
    print("Custom level creation demonstrated!")
    print("\nKey components:")
    print("  - objects: dict of Ball, Bar, Basket objects")
    print("  - action_objects: list of user-placeable object names")
    print("  - success_condition: function(engine) -> bool")
    print("  - PhyreEnv.from_level(level) to run")
    print("=" * 50)


if __name__ == "__main__":
    main()
