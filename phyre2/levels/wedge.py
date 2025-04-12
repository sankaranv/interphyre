import numpy as np
from typing import cast
from phyre2.objects import Ball, Basket, Platform, PhyreObject
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):

    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_platform", success_time
    )


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    green_ball_radius = 0.4
    green_ball = Ball(
        x=rng.uniform(-2.25, 2.25),
        y=5 - green_ball_radius,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    red_ball_radius = rng.uniform(0.5, 1.0)
    red_ball = Ball(
        x=rng.uniform(-2.25, 2.25),
        y=rng.uniform(0, 4),
        radius=red_ball_radius,
        color="red",
        dynamic=True,
    )

    corner_point_x = rng.uniform(-3, 3)
    corner_point_y = rng.uniform(-2, 2)
    height_gap = red_ball_radius - 0.1
    width_gap = 2 * rng.uniform(green_ball_radius, red_ball_radius)

    purple_platform_angle = rng.uniform(5, 20)
    purple_platform_length = (
        np.abs(5 - corner_point_x) / np.cos(np.radians(purple_platform_angle))
        - width_gap / 2
    )
    purple_platform_x = (
        corner_point_x
        + np.cos(np.radians(purple_platform_angle)) * purple_platform_length / 2
    ) + width_gap / 2

    purple_platform_y = (
        corner_point_y
        + np.sin(np.radians(purple_platform_angle)) * purple_platform_length / 2
    ) - height_gap / 2

    purple_platform = Platform(
        x=purple_platform_x,
        y=purple_platform_y,
        length=purple_platform_length,
        angle=purple_platform_angle,
        color="purple",
        dynamic=False,
    )

    black_platform_angle = rng.uniform(5, 20)
    black_platform_horiz_dist = np.abs(corner_point_x - (-5))
    black_platform_length = (
        black_platform_horiz_dist / np.cos(np.radians(black_platform_angle))
        - width_gap / 2
    )
    black_platform_x = (corner_point_x + (-5)) / 2 - width_gap / 2
    black_platform_y = (
        corner_point_y
        + np.sin(np.radians(black_platform_angle)) * black_platform_length / 2
    ) + height_gap / 2
    black_platform = Platform(
        x=black_platform_x,
        y=black_platform_y,
        length=black_platform_length,
        angle=180 - black_platform_angle,
        color="black",
        dynamic=False,
    )

    # Assemble objects dictionary.
    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "purple_platform": purple_platform,
        "black_platform": black_platform,
    }

    return Level(
        name="wedge",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball wedged onto the purple platform"},
    )


register_level("wedge")(build_level)
