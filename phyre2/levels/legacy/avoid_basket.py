import numpy as np
from typing import cast
from phyre2.objects import Ball, Basket, Platform, PhyreObject
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):
    # Success is defined as:
    # - The green_ball is in contact with the purple_platform (ground contact)
    # - AND the green_ball is NOT in contact with the basket.
    return engine.has_contact("green_ball", "purple_platform") and (
        not engine.has_contact("green_ball", "basket")
    )


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    # Create objects with initial fixed values (which will then be randomized).
    green_ball = Ball(
        x=0.0,
        y=4.9,
        radius=1.0,
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
        y=-4.9,
        length=5.0,
        angle=0.0,
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

    # Randomly set green ball attributes.
    green_ball.x = rng.uniform(-4.5, 4.5)
    green_ball.y = rng.uniform(0.5, 4.5)
    green_ball.radius = rng.uniform(0.2, 0.5)

    # Set basket starting position based on green_ball.
    basket.x = green_ball.x
    basket.y = -4.9 + basket.scale + rng.uniform(0, 1)
    basket.scale = rng.uniform(0.5, 1.5)

    # Randomly set red ball starting position.
    red_ball.x = rng.uniform(-4.5, 4.5)
    red_ball.y = rng.uniform(-2, 4)

    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "purple_platform": purple_platform,
        "basket": basket,
    }

    return Level(
        name="avoid_basket",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        target_object="green_ball",
        goal_object="purple_platform",
        success_condition=success_condition,
        metadata={
            "description": "Make sure the green ball hits the ground and stays out of the basket"
        },
    )


register_level("avoid_basket")(build_level)
