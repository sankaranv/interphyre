import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, Basket, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.render import MIN_X, MAX_X, MIN_Y, MAX_Y


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_bar", "purple_ground", success_time)


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    black_platform_center_x = rng.uniform(-2.5, 2.5)
    max_platform_length = 10.0 - 2 * 0.3 - 2 * abs(black_platform_center_x)
    min_platform_length = 4.0
    black_platform_length = rng.uniform(min_platform_length, max_platform_length)
    black_platform_y = rng.uniform(-3, 1)

    black_platform = Bar(
        left=black_platform_center_x - black_platform_length / 2,
        right=black_platform_center_x + black_platform_length / 2,
        y=black_platform_y,
        color="black",
        dynamic=False,
    )

    ceiling_y = rng.uniform(max(2, black_platform_y + 0.4), 4.8)
    max_bar_length = ceiling_y - black_platform_y - 0.4
    # Set a reasonable minimum height
    min_bar_length = 1.5
    # Ensure max_bar_length is at least min_bar_length
    max_bar_length = max(max_bar_length, min_bar_length)
    green_bar_length = rng.uniform(min_bar_length, max_bar_length)

    # Position the green bar exactly at the edge of the black platform
    # Since platform positions are at their centers, we need to account for this
    # The edge of the black platform is at black_platform_center_x ± black_platform_length/2
    # We want the center of the green bar to be at this edge
    green_bar_x = black_platform_center_x + (
        rng.choice([-1, 1]) * (black_platform_length / 2 - 0.1)
    )

    # For the y-position, we want the bottom of the green bar to be at the top of the black platform
    # The top of the black platform is at black_platform_y + thickness/2
    # The bottom of the green bar is at green_bar_bottom
    # So we set green_bar_bottom = black_platform_y + thickness/2
    green_bar_bottom = black_platform_y + 0.2 / 2  # thickness/2
    green_bar_top = green_bar_bottom + green_bar_length

    green_bar = Bar.from_point_and_angle(
        x=green_bar_x,
        y=(green_bar_top + green_bar_bottom) / 2,  # Center y position
        angle=90.0,  # Vertical bar
        length=green_bar_length,
        thickness=0.2,
        color="green",
        dynamic=True,
    )

    # Ceiling (horizontal)
    ceiling = Bar(
        left=MIN_X,
        right=MAX_X,
        y=ceiling_y,
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

    # Purple ground (horizontal)
    purple_ground = Bar(
        left=MIN_X,
        right=MAX_X,
        y=MIN_Y + 0.2 / 2,  # thickness/2 from bottom
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

    # Set up the level
    return Level(
        name="cliffhanger",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Tip over the bar so it hits the ground.",
        },
    )
