import numpy as np
from typing import cast
from interphyre.objects import Ball, Basket, Bar, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level


def success_condition(engine):

    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_platform", success_time
    )


@register_level
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

    gap_center_x = rng.uniform(-3, 3)
    gap_center_y = rng.uniform(-2, 2)
    height_gap = rng.uniform(0.5, 1.0) - 0.1
    width_gap = 2 * rng.uniform(green_ball_radius, 2 * green_ball_radius)

    purple_platform_angle = rng.uniform(5, 20)

    # Purple platform: from right end of gap to right wall
    purple_platform_start_x = gap_center_x + width_gap / 2
    purple_platform_start_y = gap_center_y - height_gap / 2
    purple_platform_end_x = 5
    purple_platform_end_y = (
        gap_center_y
        - height_gap / 2
        + (purple_platform_end_x - purple_platform_start_x)
        * np.tan(np.radians(purple_platform_angle))
    )

    purple_platform = Bar.from_endpoints(
        x1=purple_platform_start_x,
        y1=purple_platform_start_y,
        x2=purple_platform_end_x,
        y2=purple_platform_end_y,
        thickness=0.2,
        color="purple",
        dynamic=False,
    )

    black_platform_angle = rng.uniform(5, 20)

    # Black platform: from left wall to left end of gap
    black_platform_start_x = -5
    black_platform_start_y = (
        gap_center_y
        + height_gap / 2
        + (gap_center_x - black_platform_start_x)
        * np.tan(np.radians(black_platform_angle))
    )
    black_platform_end_x = gap_center_x - width_gap / 2
    black_platform_end_y = gap_center_y + height_gap / 2

    black_platform = Bar.from_endpoints(
        x1=black_platform_start_x,
        y1=black_platform_start_y,
        x2=black_platform_end_x,
        y2=black_platform_end_y,
        thickness=0.2,
        color="black",
        dynamic=False,
    )

    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "purple_platform": purple_platform,
        "black_platform": black_platform,
    }

    return Level(
        name="wedge_issue",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball wedged onto the purple platform"},
    )
