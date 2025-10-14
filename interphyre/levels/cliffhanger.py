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
    min_bar_length = 1.5
    max_bar_length = max(max_bar_length, min_bar_length)
    green_bar_length = rng.uniform(min_bar_length, max_bar_length)
    green_bar_x = black_platform_center_x + (
        rng.choice([-1, 1]) * (black_platform_length / 2 - 0.1)
    )
    green_bar_bottom = black_platform_y + 0.2 / 2
    green_bar_top = green_bar_bottom + green_bar_length

    green_bar = Bar.from_point_and_angle(
        x=green_bar_x,
        y=(green_bar_top + green_bar_bottom) / 2,
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
