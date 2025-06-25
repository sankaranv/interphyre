import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, PhyreObject, Basket
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.render import MAX_Y


def success_condition(engine):
    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "purple_pad", success_time)


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    floor = Bar(
        x=0.0,
        y=-4.9,
        length=10.0,
        angle=0,
        color="black",
        dynamic=False,
    )

    green_ball_radius = gray_ball_radius = 0.4
    green_ball_x = gray_ball_x = rng.uniform(-4, 4)
    green_ball_y = MAX_Y - green_ball_radius
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    gray_ball_y = green_ball_y - rng.uniform(0.5, 2)
    gray_ball = Ball(
        x=gray_ball_x,
        y=gray_ball_y,
        radius=gray_ball_radius,
        color="gray",
        dynamic=True,
    )

    purple_pad_length = rng.uniform(1, 2.5)
    purple_pad_x = rng.uniform(-4, 4)
    purple_pad = Bar(
        x=purple_pad_x,
        y=-4.7,
        length=purple_pad_length,
        angle=0,
        color="purple",
        dynamic=False,
    )

    pad_left_rim = Bar(
        x=purple_pad_x - purple_pad_length / 2 - 0.1,
        y=-4.5,
        length=0.2,
        angle=0,
        color="black",
        dynamic=False,
    )

    pad_right_rim = Bar(
        x=purple_pad_x + purple_pad_length / 2 + 0.1,
        y=-4.5,
        length=0.2,
        angle=0,
        color="black",
        dynamic=False,
    )

    red_ball = Ball(
        x=0.0,
        y=0.0,
        radius=rng.uniform(0.6, 1.2),
        color="red",
        dynamic=True,
    )

    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "gray_ball": gray_ball,
        "purple_pad": purple_pad,
        "pad_left_rim": pad_left_rim,
        "pad_right_rim": pad_right_rim,
        "floor": floor,
    }

    return Level(
        name="straight_face",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={"description": "Knock the green ball onto the purple pad"},
    )
