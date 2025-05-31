import numpy as np
from typing import cast
from phyre2.objects import Ball, Bar, PhyreObject
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):
    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "purple_pad", success_time)


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    green_ball_radius = 0.3
    green_ball = Ball(
        x=rng.uniform(-1.0, 1.0),
        y=(5 - green_ball_radius),
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )
    red_ball = Ball(
        x=0.0,
        y=0.0,
        radius=0.4,
        color="red",
        dynamic=True,
    )
    # Generate random angle between 15 and 35 degrees
    funnel_angle = rng.uniform(10.0, 35.0)

    # Safety margin to prevent ceiling clipping
    safety_margin = 0.5

    height_offset = rng.uniform(-1.0, 1.0)
    funnel_y = 2 + height_offset
    funnel_x = 3 + rng.uniform(0, 0.25)
    # Calculate required length to reach walls (-5 to 5) while maintaining minimum gap
    # The gap at the bottom of the funnel should be at least 0.5
    # Using trigonometry: length = (wall_distance - gap/2) / cos(angle)
    wall_distance = 5.0  # Distance from center to wall
    funnel_length = wall_distance / np.cos(np.radians(funnel_angle))

    left_funnel = Bar(
        x=-funnel_x,
        y=funnel_y,
        length=funnel_length,
        angle=-funnel_angle,
        color="black",
        dynamic=False,
    )
    right_funnel = Bar(
        x=funnel_x,
        y=funnel_y,
        length=funnel_length,
        angle=funnel_angle,
        color="black",
        dynamic=False,
    )

    corner_pos = rng.choice([-1.0, 1.0])
    purple_pad = Bar(
        x=corner_pos * 4.0,
        y=-4.9,
        length=2.0,
        angle=0.0,
        color="purple",
        dynamic=False,
    )
    ground = Bar(
        x=-corner_pos,
        y=-4.9,
        length=8.0,
        angle=0.0,
        color="black",
        dynamic=False,
    )
    black_pad = Bar(
        x=corner_pos * 2.0,
        y=-4.7,
        length=2.0,
        angle=0.0,
        color="black",
        dynamic=False,
    )

    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "left_funnel": left_funnel,
        "right_funnel": right_funnel,
        "black_pad": black_pad,
        "purple_pad": purple_pad,
        "ground": ground,
    }

    return Level(
        name="the_funnel",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Make sure the green ball goes through the funnel and hits the purple pad"
        },
    )
