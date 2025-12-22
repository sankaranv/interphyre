import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.render import MIN_X, MAX_X, MIN_Y


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_bar",
        "purple_ground",
        success_time,
    )


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    black_platform_center_x = rng.uniform(-2.5, 2.5)
    max_platform_length = 10.0 - 2 * 0.3 - 2 * abs(black_platform_center_x)
    min_platform_length = 4.0
    black_platform_length = rng.uniform(
        min_platform_length,
        max_platform_length,
    )
    black_platform_y = rng.uniform(-3, 1)

    black_platform = Bar.from_point_and_angle(
        x=black_platform_center_x,
        y=black_platform_y,
        length=black_platform_length,
        angle=0,
        color="black",
        dynamic=False,
    )

    # Ensure feasibility: require at least `clearance` between the green bar's
    # top and the bottom of the ceiling bar. The ceiling has thickness, so its
    # edge is at ceiling_y - ceiling_thickness/2.
    min_bar_length = 1.5
    clearance = 0.5
    ceiling_thickness = 0.2
    min_ceiling_y = max(
        2,
        black_platform_y + 0.1 + min_bar_length + clearance + ceiling_thickness / 2,
    )
    ceiling_y = rng.uniform(min_ceiling_y, 4.8)
    max_bar_length = (
        ceiling_y - (ceiling_thickness / 2) - black_platform_y - 0.1 - clearance
    )
    green_bar_length = rng.uniform(min_bar_length, max_bar_length)

    # Position green bar at edge of platform
    edge_offset = (black_platform_length / 2 - 0.1) * rng.choice([-1, 1])
    green_bar_x = black_platform_center_x + edge_offset
    green_bar_y = black_platform_y + 0.1 + green_bar_length / 2

    green_bar = Bar.from_point_and_angle(
        x=green_bar_x,
        y=green_bar_y,
        angle=90.0,
        length=green_bar_length,
        thickness=0.2,
        color="green",
        dynamic=True,
    )

    ceiling = Bar(
        left=MIN_X,
        right=MAX_X,
        y=ceiling_y,
        thickness=ceiling_thickness,
        color="black",
        dynamic=False,
    )

    red_ball = Ball(
        x=rng.uniform(-4.5, 4.5),
        y=rng.uniform(-2, 4),
        radius=rng.uniform(0.4, 0.8),
        color="red",
        dynamic=True,
    )

    purple_ground = Bar(
        left=MIN_X,
        right=MAX_X,
        y=MIN_Y + 0.2 / 2,
        color="purple",
        dynamic=False,
    )

    objects = {
        "black_platform": black_platform,
        "green_bar": green_bar,
        "ceiling": ceiling,
        "red_ball": red_ball,
        "purple_ground": purple_ground,
    }

    return Level(
        name="cliffhanger",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Tip over the green bar so it hits the purple ground.",
        },
    )
