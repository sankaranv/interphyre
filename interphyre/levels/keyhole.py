import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, PhyreObject, Basket
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.render import MAX_X, MAX_Y, MIN_Y


def success_condition(engine):
    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "purple_pad", success_time)


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

    gap_height = rng.uniform(2.5, 4.5)
    gap_width = rng.uniform(0.5, 1)
    room_height = MAX_Y - MIN_Y
    top_divider = Bar(
        x=0,
        y=MAX_Y - (room_height - gap_height) / 2,
        length=room_height - gap_height,
        angle=90,
        color="black",
        dynamic=False,
    )
    green_ball_radius = np.clip(
        (
            rng.uniform(
                min(gap_width / 2, gap_height / 2), max(gap_width / 2, gap_height / 2)
            )
            - 0.05
        ),
        None,
        0.7,
    )

    bottom_divider_x = rng.uniform(2 * green_ball_radius + 0.1, 3.5) * np.sign(
        -purple_pad_x
    )
    bottom_divider_length = (gap_height - 2 * green_ball_radius) * rng.uniform(0.75, 1)
    bottom_divider_y = MIN_Y + (bottom_divider_length) / 2
    green_ball_offset = rng.uniform(
        green_ball_radius, (MAX_X - np.abs(bottom_divider_x)) * 0.5
    )
    green_ball_x = (np.abs(bottom_divider_x) + green_ball_offset) * np.sign(
        bottom_divider_x
    )
    green_ball_y = rng.uniform(bottom_divider_y + gap_height / 2, MAX_Y)
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    bottom_divider = Bar(
        x=bottom_divider_x,
        y=bottom_divider_y,
        length=bottom_divider_length,
        angle=90,
        color="black",
        dynamic=False,
    )

    red_ball = Ball(
        x=0,
        y=-4.5,
        radius=rng.uniform(0.5, 1),
        color="red",
        dynamic=True,
    )

    objects = {
        "purple_pad": purple_pad,
        "black_pad": black_pad,
        "top_divider": top_divider,
        "bottom_divider": bottom_divider,
        "green_ball": green_ball,
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
