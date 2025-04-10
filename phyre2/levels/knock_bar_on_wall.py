import numpy as np
from typing import cast
from phyre2.objects import Ball, Basket, Platform, PhyreObject
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):
    # Define success: the green_platform must contact the purple_platform (the wall).
    return engine.has_contact("green_platform", "purple_platform")


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    # Create base objects with initial fixed values.
    green_platform = Platform(
        x=0.0,
        y=-4.5,
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
        length=10.0,
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
    # target_object is green_platform, goal_object is purple_platform,
    # and the action object is red_ball.
    #
    # Randomly set purple_platform's x coordinate (simulate left/right wall).
    purple_platform.x = rng.choice([-4.9, 4.9])

    # Randomly adjust green_platform's attributes.
    green_platform.x = rng.uniform(-2, 2)
    green_platform.length = rng.uniform(1, 4)
    # Position green_platform so that its bottom aligns with the floor at y = -4.9.
    green_platform.y = -4.9 + green_platform.length / 2

    # Set basket x to be equal to green_platform's x.
    basket.x = green_platform.x

    # Randomly set red_ball's starting position.
    red_ball.x = rng.uniform(-4.5, 4.5)
    red_ball.y = rng.uniform(-2, 4)

    objects = {
        "green_platform": green_platform,
        "red_ball": red_ball,
        "purple_platform": purple_platform,
        "basket": basket,
    }

    return Level(
        name="knock_bar_on_wall",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        target_object="green_platform",
        goal_object="purple_platform",
        success_condition=success_condition,
        metadata={"description": "Make the green ball hit the left or right wall"},
    )


register_level("knock_bar_on_wall")(build_level)
