import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
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

    funnel_angle = rng.uniform(10.0, 35.0)
    height_offset = rng.uniform(-1.0, 1.0)
    funnel_y = 2 + height_offset
    funnel_x = 3 + rng.uniform(0, 0.25)
    wall_distance = 5.0
    funnel_length = wall_distance / np.cos(np.radians(funnel_angle))

    left_funnel = Bar.from_point_and_angle(
        x=-funnel_x,
        y=funnel_y,
        angle=-funnel_angle,
        length=funnel_length,
        thickness=0.2,
        color="black",
        dynamic=False,
    )
    right_funnel = Bar.from_point_and_angle(
        x=funnel_x,
        y=funnel_y,
        angle=funnel_angle,
        length=funnel_length,
        thickness=0.2,
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
