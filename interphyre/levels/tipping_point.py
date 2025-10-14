import numpy as np
from typing import cast
from interphyre.objects import Ball, Basket, Bar, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.render import MIN_X, MAX_X


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_platform", "purple_wall", success_time
    )


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    green_platform_length = rng.uniform(2, 7)
    buffer = 0.25
    # Randomly choose left or right side
    if rng.choice([True, False]):
        green_platform_x = rng.uniform(
            MIN_X + 1 + buffer, MIN_X + green_platform_length - buffer
        )
        purple_wall_x = -4.9
    else:
        green_platform_x = rng.uniform(
            MAX_X - green_platform_length + buffer, MAX_X - 1 - buffer
        )
        purple_wall_x = 4.9

    green_platform_y = -4.9 + green_platform_length / 2
    green_platform = Bar.from_point_and_angle(
        x=green_platform_x,
        y=green_platform_y,
        length=green_platform_length,
        angle=90.0,
        thickness=0.2,
        color="green",
        dynamic=True,
    )

    basket = Basket(
        x=green_platform_x,
        y=-4.9,
        scale=0.5,
        wall_thickness=0.15,
        friction=1.2,
        restitution=0.1,
        linear_damping=1.0,
        anchor="bottom_center",
        color="gray",
        dynamic=True,
    )

    purple_wall = Bar.from_point_and_angle(
        x=purple_wall_x,
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
        name="tipping_point",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball hit the left or right wall"},
    )
