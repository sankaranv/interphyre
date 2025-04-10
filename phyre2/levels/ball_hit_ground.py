import numpy as np
from typing import cast
from phyre2.objects import Ball, Platform, Basket, PhyreObject
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):
    # Define success as the green ball contacting the purple platform (the ground).
    return engine.is_in_contact_for_duration("green_ball", "purple_ground", 3)


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    # Create the purple platform (goal/ground).
    purple_ground = Platform(
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
    high_platform = Platform(
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
        name="ball_hit_ground",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        target_object="green_ball",
        goal_object="purple_ground",
        success_condition=success_condition,
        metadata={"description": "Make the green ball hit the ground"},
    )


register_level("ball_hit_ground")(build_level)
