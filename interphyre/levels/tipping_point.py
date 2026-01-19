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

    green_platform_length = rng.uniform(2, 6)
    buffer = 0.25
    # Randomly choose left or right side
    if rng.choice([True, False]):
        # Left side - platform near left wall
        green_platform_x = rng.uniform(
            MIN_X + green_platform_length / 2 + buffer,
            MIN_X + green_platform_length / 2 + 2
        )
        purple_wall_x = -4.9
    else:
        # Right side - platform near right wall
        green_platform_x = rng.uniform(
            MAX_X - green_platform_length / 2 - 2,
            MAX_X - green_platform_length / 2 - buffer
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
        thickness=0.2,
        color="purple",
        dynamic=False,
    )

    # Position red ball away from basket to avoid trivial solutions
    red_ball_radius = rng.uniform(0.4, 0.9)
    min_distance_from_basket = basket.top_width / 2 + red_ball_radius + 0.5

    attempts = 0
    while attempts < 100:
        red_ball_x = rng.uniform(-4.5, 4.5)
        red_ball_y = rng.uniform(-2, 4)
        # Ensure red ball not directly above basket
        if abs(red_ball_x - green_platform_x) > min_distance_from_basket:
            break
        attempts += 1

    red_ball = Ball(
        x=red_ball_x,
        y=red_ball_y,
        radius=red_ball_radius,
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
        metadata={"description": "Make the green platform hit the left or right wall"},
    )
