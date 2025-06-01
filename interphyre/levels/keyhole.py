import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, PhyreObject, Basket
from interphyre.level import Level
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    purple_pad_x = rng.choice([-2.5, 2.5])
    purple_pad = Bar(
        x=purple_pad_x,
        y=-4.9,
        length=5,
        angle=0,
        color="purple",
        dynamic=False,
    )
    black_pad = Bar(
        x=-purple_pad_x,
        y=-4.9,
        length=5,
        angle=0,
        color="black",
        dynamic=False,
    )

    red_ball = Ball(
        x=0,
        y=-4.5,
        radius=0.4,
        color="red",
        dynamic=True,
    )

    objects = {
        "purple_pad": purple_pad,
        "black_pad": black_pad,
        # "floor_barrier": floor_barrier,
        # "ceiling_barrier": ceiling_barrier,
        # "green_ball": green_ball,
        "red_ball": red_ball,
    }

    return Level(
        name="keyhole",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Push the basket so the green ball falls in and hits the blue ball"
        },
    )
