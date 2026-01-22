import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.config import MIN_X, MAX_X, MAX_Y


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_platform", success_time
    )


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    green_ball_radius = 0.3
    green_ball = Ball(
        x=rng.uniform(-2.25, 2.25),
        y=MAX_Y - green_ball_radius,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    gap_center_x = rng.uniform(-3, 3)
    gap_center_y = rng.uniform(-2, 2)
    height_gap = rng.uniform(0.4, 0.9)
    width_gap = rng.uniform(2 * green_ball_radius, 4 * green_ball_radius)

    purple_platform_angle = rng.uniform(5, 20)
    purple_platform_start_x = gap_center_x + width_gap / 2
    purple_platform_start_y = gap_center_y - height_gap / 2
    purple_platform_end_x = MAX_X
    purple_platform_end_y = (
        purple_platform_start_y
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
    black_platform_end_x = gap_center_x - width_gap / 2
    black_platform_end_y = gap_center_y + height_gap / 2
    black_platform_start_x = MIN_X
    black_platform_start_y = (
        black_platform_end_y
        + (black_platform_end_x - black_platform_start_x)
        * np.tan(np.radians(black_platform_angle))
    )

    black_platform = Bar.from_endpoints(
        x1=black_platform_start_x,
        y1=black_platform_start_y,
        x2=black_platform_end_x,
        y2=black_platform_end_y,
        thickness=0.2,
        color="black",
        dynamic=False,
    )

    red_ball_radius = rng.uniform(0.3, 0.6)
    red_ball = Ball(
        x=0.0,
        y=0.0,
        radius=red_ball_radius,
        color="red",
        dynamic=True,
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
