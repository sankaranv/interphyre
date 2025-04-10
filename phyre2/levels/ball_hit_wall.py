import numpy as np
from typing import cast
from phyre2.objects import Ball, Basket, Platform, PhyreObject
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):
    # Level designers define success via object names.
    # Here, when the "green_platform" (target) contacts "purple_platform" (goal),
    # we consider the level complete.
    return engine.has_contact("green_platform", "purple_platform")


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    # Create objects with base fixed parameters (later randomized).
    green_platform = Platform(
        x=0.0,
        y=-4.8,
        length=1.0,
        angle=90.0,
        color="green",
        dynamic=True,
    )
    red_ball = Ball(
        x=0.0,
        y=0.0,
        radius=0.4,
        color="red",
        dynamic=True,
    )
    purple_platform = Platform(
        x=0.0,
        y=0.0,
        length=5.0,
        angle=90.0,
        color="purple",
        dynamic=False,
    )
    basket = Basket(
        x=0.0,
        y=-4.9,
        scale=1.0,
        color="gray",
        dynamic=True,
    )

    # Set level properties:
    #   target_object: green_platform
    #   goal_object: purple_platform
    #   action_objects: red_ball
    #
    # Randomly place the purple platform on the left or right (simulate a wall).
    purple_platform.x = rng.choice([-4.9, 4.9])

    # Randomly adjust the green platform (acting as our "ball" target).
    green_platform.x = rng.uniform(-2, 2)
    green_platform.length = rng.uniform(1, 4)
    # Place green_platform so that its center is adjusted from a baseline of -4.9.
    green_platform.y = -4.9 + green_platform.length / 2

    # Set the basket to align horizontally with the green platform.
    basket.x = green_platform.x

    # Randomly set red ball starting position.
    red_ball.x = rng.uniform(-4.5, 4.5)
    red_ball.y = rng.uniform(-2, 4)

    objects = {
        "green_platform": green_platform,
        "red_ball": red_ball,
        "purple_platform": purple_platform,
        "basket": basket,
    }

    return Level(
        name="ball_hit_wall",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        target_object="green_platform",
        goal_object="purple_platform",
        success_condition=success_condition,
        metadata={"description": "Make the green ball hit the left or right wall"},
    )


register_level("ball_hit_wall")(build_level)
