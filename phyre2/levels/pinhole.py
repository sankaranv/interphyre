import numpy as np
from typing import cast
from phyre2.objects import Ball, Platform, Basket, PhyreObject
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):

    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_ground", success_time
    )


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    purple_ground = Platform(
        x=0.0,
        y=-4.9,
        length=10.0,
        thickness=0.2,
        angle=0.0,
        color="purple",
        dynamic=False,
    )

    pinhole_x = rng.choice([rng.uniform(-3, -0.25), rng.uniform(0.25, 3)])

    green_ball_radius = 0.4
    green_ball_x = np.clip(pinhole_x + rng.uniform(-2, 2), -4, 4)
    green_ball_y = rng.uniform(3, 5 - green_ball_radius)
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    pinhole_width = 2 * green_ball_radius + 0.1
    platform_y = rng.uniform(-2, 2)

    left_gap_edge = pinhole_x - pinhole_width / 2
    left_platform_length = left_gap_edge - (-5)
    left_platform_x = -5 + left_platform_length / 2

    right_gap_edge = pinhole_x + pinhole_width / 2
    right_platform_length = 5 - right_gap_edge
    right_platform_x = 5 - right_platform_length / 2

    left_platform = Platform(
        x=left_platform_x,
        y=platform_y,
        length=left_platform_length,
        thickness=0.2,
        angle=0.0,
        color="black",
        dynamic=False,
    )

    right_platform = Platform(
        x=right_platform_x,
        y=platform_y,
        length=right_platform_length,
        thickness=0.2,
        angle=0.0,
        color="black",
        dynamic=False,
    )

    gray_ball_radius = 0.5
    gray_ball_x = pinhole_x + rng.uniform(-1, 1)
    gray_ball_y = rng.uniform(
        platform_y + gray_ball_radius, green_ball_y - gray_ball_radius
    )
    gray_ball = Ball(
        x=gray_ball_x,
        y=gray_ball_y,
        radius=gray_ball_radius,
        color="gray",
        dynamic=True,
    )
    # Create the red ball (action object).
    red_ball_x = rng.uniform(-4.5, 4.5)
    red_ball_y = rng.uniform(-2, 4)
    red_ball_radius = rng.uniform(0.3, 0.7)
    red_ball = Ball(
        x=red_ball_x,
        y=red_ball_y,
        radius=red_ball_radius,
        color="red",
        dynamic=True,
    )

    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "gray_ball": gray_ball,
        "purple_ground": purple_ground,
        "left_platform": left_platform,
        "right_platform": right_platform,
    }

    return Level(
        name="pinhole",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball hit the ground"},
    )


register_level("pinhole")(build_level)
