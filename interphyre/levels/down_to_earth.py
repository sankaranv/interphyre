import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, Basket, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level


def success_condition(engine):

    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_ground", success_time
    )


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    # Create the purple ground.
    purple_ground = Bar(
        x=0.0,
        y=-4.9,
        length=10.0,
        thickness=0.2,
        angle=0.0,
        color="purple",
        dynamic=False,
    )

    # Create the high platform.
    # Make the x position more likely to be at the ends than the middle
    platform_length = rng.uniform(3, 7)
    platform_x = rng.beta(0.5, 0.5) * platform_length - platform_length / 2
    platform_y = rng.uniform(-1, 3)
    high_platform = Bar(
        x=platform_x,
        y=platform_y,
        length=platform_length,
        thickness=0.2,
        angle=0.0,
        color="black",
        dynamic=False,
    )

    # Make the ball land in the middle of the platform
    green_ball_radius = 0.5
    green_ball_x = platform_x
    green_ball_y = 4.9
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    # Create the red ball (action object).
    red_ball_x = rng.uniform(-4.5, 4.5)
    red_ball_y = rng.uniform(-2, 4)
    red_ball_radius = rng.uniform(0.4, 0.8)
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
        "purple_ground": purple_ground,
        "high_platform": high_platform,
    }

    return Level(
        name="down_to_earth",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball hit the ground"},
    )
