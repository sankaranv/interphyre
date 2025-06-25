import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, PhyreObject, Basket
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.render import MAX_Y


def success_condition(engine):
    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "purple_floor", success_time)


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    purple_floor = Bar(
        x=0.0,
        y=-4.9,
        length=10.0,
        angle=0,
        color="purple",
        dynamic=False,
    )

    green_ball_radius = 0.4
    green_ball_x = rng.uniform(-4, 4)
    green_ball_y = rng.uniform(-3, 3)
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    holder_length = rng.uniform(0.4, 1)
    holder_gap = 0.04
    holder_angle = rng.uniform(5, 10)
    left_holder = Bar(
        x=green_ball_x - holder_length / 2 - holder_gap / 2,
        y=green_ball_y - green_ball_radius - 0.1,
        length=holder_length,
        angle=-holder_angle,
        color="black",
        dynamic=False,
    )

    right_holder = Bar(
        x=green_ball_x + holder_length / 2 + holder_gap / 2,
        y=green_ball_y - green_ball_radius - 0.1,
        length=holder_length,
        angle=holder_angle,
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
        "left_holder": left_holder,
        "right_holder": right_holder,
        "purple_floor": purple_floor,
    }

    return Level(
        name="the_cradle",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={"description": "Push the green ball onto the purple floor"},
    )
