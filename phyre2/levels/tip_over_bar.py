import numpy as np
from typing import cast
from phyre2.objects import Ball, Platform, Basket, PhyreObject
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):
    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration("green_bar", "purple_ground", success_time)


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    black_platform_x = rng.uniform(-2.5, 2.5)
    # Calculate maximum possible length with 0.3 gap from each wall
    max_platform_length = 10.0 - 2 * 0.3 - 2 * abs(black_platform_x)
    # Set a reasonable minimum length
    min_platform_length = 4.0
    # Randomly select a length between min and max
    black_platform_length = rng.uniform(min_platform_length, max_platform_length)
    black_platform_y = rng.uniform(-3, 1)

    black_platform = Platform(
        x=black_platform_x,
        y=black_platform_y,
        length=black_platform_length,
        angle=0.0,
        thickness=0.2,
        color="black",
        dynamic=False,
    )

    # Randomize ceiling platform height
    ceiling_y = rng.uniform(max(2, black_platform_y + 0.4), 4.8)

    # Calculate maximum possible height with 0.2 gap from ceiling
    max_bar_length = ceiling_y - black_platform_y - 0.4
    # Set a reasonable minimum height
    min_bar_length = 1.5
    # Randomly select a height between min and max
    green_bar_length = rng.uniform(min_bar_length, max_bar_length)

    # Position the green bar exactly at the edge of the black platform
    # Since platform positions are at their centers, we need to account for this
    # The edge of the black platform is at black_platform.x ± black_platform.length/2
    # We want the center of the green bar to be at this edge
    green_bar_x = black_platform.x + (
        rng.choice([-1, 1]) * (black_platform.length / 2 - 0.1)
    )

    # For the y-position, we want the bottom of the green bar to be at the top of the black platform
    # The top of the black platform is at black_platform.y + black_platform.thickness/2
    # The bottom of the green bar is at green_bar_y - green_bar_length/2
    # So we set green_bar_y - green_bar_length/2 = black_platform.y + black_platform.thickness/2
    # Therefore, green_bar_y = black_platform.y + black_platform.thickness/2 + green_bar_length/2
    green_bar_y = black_platform.y + black_platform.thickness / 2 + green_bar_length / 2

    green_bar = Platform(
        x=green_bar_x,
        y=green_bar_y,
        length=green_bar_length,
        angle=90.0,
        thickness=0.2,
        color="green",
        dynamic=True,
    )

    ceiling = Platform(
        x=0.0,
        y=ceiling_y,
        length=10.0,
        angle=0.0,
        thickness=0.2,
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

    purple_ground = Platform(
        x=0.0,
        y=-4.9,
        length=10.0,
        angle=0.0,
        thickness=0.2,
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
        name="tip_over_bar",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Tip over the bar so it hits the ground.",
        },
    )


register_level("tip_over_bar")(build_level)
