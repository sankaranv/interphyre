import numpy as np
from typing import cast
from phyre2.objects import Ball, Platform, Basket, PhyreObject
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):
    # Define success as the green ball contacting the purple platform (the ground).
    return engine.has_contact("green_ball", "purple_platform")


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    # Create the green ball (target) with initial fixed parameters.
    green_ball = Ball(
        x=0.0,
        y=4.9,
        radius=1.0,
        color="green",
        dynamic=True,
    )

    # Create the red ball (action object).
    red_ball = Ball(
        x=0.0,
        y=0.0,
        radius=0.5,
        color="red",
        dynamic=True,
    )

    # Create the purple platform (goal/ground).
    purple_platform = Platform(
        x=0.0,
        y=-4.9,
        length=10.0,
        angle=0.0,
        color="purple",
        dynamic=False,
    )

    # Create the high platform.
    high_platform = Platform(
        x=0.0,
        y=0.0,
        length=1.0,
        angle=0.0,
        color="black",
        dynamic=False,
    )

    # Randomize high platform attributes.
    high_platform.x = rng.uniform(-2, 2)
    high_platform.y = rng.uniform(-3, 3)
    high_platform.length = rng.uniform(0.5, 2)

    # Adjust green ball's attributes:
    # Place the green ball at half the high platform's x and randomize its radius.
    green_ball.x = high_platform.x / 2
    green_ball.radius = rng.uniform(0.2, 0.45)

    # Randomize red ball's starting position.
    red_ball.x = rng.uniform(-4.5, 4.5)
    red_ball.y = rng.uniform(-2, 4)

    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "purple_platform": purple_platform,
        "high_platform": high_platform,
    }

    return Level(
        name="ball_hit_ground",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        target_object="green_ball",
        goal_object="purple_platform",
        success_condition=success_condition,
        metadata={"description": "Make the green ball hit the ground"},
    )


register_level("ball_hit_ground")(build_level)
