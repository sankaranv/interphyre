import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.levels.two_ball._constants import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("left_stick", "right_stick", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    stick_length_options = np.linspace(0.2, 0.5, 10)
    stick_x_options = np.linspace(0.05, 0.95, 19)

    while True:
        stick_length = rng.choice(stick_length_options)
        stick1_x = rng.choice(stick_x_options)
        stick2_x = rng.choice(stick_x_options)
        if stick2_x <= stick1_x + 1.75 * stick_length:
            continue
        if stick2_x > stick1_x + 2.5 * stick_length:
            continue
        break

    bar_thickness = 0.2
    stick_length_world = stick_length * WORLD_HEIGHT
    left_stick = Bar(
        top=MIN_Y + stick_length_world,
        bottom=MIN_Y,
        x=MIN_X + stick1_x * WORLD_WIDTH,
        thickness=bar_thickness,
        color="green",
        dynamic=True,
    )
    right_stick = Bar(
        top=MIN_Y + stick_length_world,
        bottom=MIN_Y,
        x=MIN_X + stick2_x * WORLD_WIDTH,
        thickness=bar_thickness,
        color="blue",
        dynamic=True,
    )

    top_bar_y = MIN_Y + (stick_length + 0.25) * WORLD_HEIGHT
    top_bar = Bar(
        left=MIN_X,
        right=MAX_X,
        y=top_bar_y + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    red_ball_1 = Ball(
        x=-3.0,
        y=4.0,
        radius=0.5,
        color="red",
        dynamic=True,
    )
    red_ball_2 = Ball(
        x=3.0,
        y=4.0,
        radius=0.5,
        color="red",
        dynamic=True,
    )

    objects = {
        "left_stick": left_stick,
        "right_stick": right_stick,
        "top_bar": top_bar,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00115",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the two sticks touch."},
    )
