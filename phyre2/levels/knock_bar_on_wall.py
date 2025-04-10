import numpy as np
from typing import cast
from phyre2.objects import Ball, Basket, Platform, PhyreObject
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):
    # Define success: the green_platform must contact the purple_wall.
    return engine.is_in_contact_for_duration("green_platform", "purple_wall", 3)


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    # Randomly adjust green_platform's attributes.
    green_platform_x = rng.uniform(-4, 4)
    green_platform_length = rng.uniform(2, 7)
    green_platform_y = -4.9 + green_platform_length / 2
    green_platform = Platform(
        x=green_platform_x,
        y=green_platform_y,
        length=green_platform_length,
        angle=90.0,
        thickness=0.15,
        color="green",
        dynamic=True,
    )

    basket = Basket(
        x=green_platform_x,
        y=-4.9,
        scale=0.5,
        color="gray",
        dynamic=True,
    )

    purple_wall = Platform(
        x=rng.choice([-4.9, 4.9]),
        y=0.0,
        length=10.0,
        angle=90.0,
        color="purple",
        dynamic=False,
    )

    red_ball = Ball(
        x=rng.uniform(-4.5, 4.5),
        y=rng.uniform(-2, 4),
        radius=rng.uniform(0.4, 0.9),
        color="red",
        dynamic=True,
    )

    objects = {
        "green_platform": green_platform,
        "red_ball": red_ball,
        "purple_wall": purple_wall,
        "basket": basket,
    }

    return Level(
        name="knock_bar_on_wall",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball hit the left or right wall"},
    )


register_level("knock_bar_on_wall")(build_level)
