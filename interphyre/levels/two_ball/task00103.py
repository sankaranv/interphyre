import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    ball_size = 0.1
    hole_left = rng.choice(np.linspace(0.1, 0.4, 7))
    hole_right = rng.choice(np.linspace(0.1, 0.4, 7))
    bottom = rng.choice(np.linspace(0.0, 0.5, 7))

    ball_radius = ball_size * (10.0) / 2
    green_ball_x = (-5.0) + hole_left * (10.0)
    blue_ball_x = (-5.0) + (1 - hole_right) * (10.0)
    green_ball_y = (-5.0) + 0.9 * (10.0) + ball_radius
    blue_ball_y = (-5.0) + 0.9 * (10.0) + ball_radius

    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )
    blue_ball = Ball(
        x=blue_ball_x,
        y=blue_ball_y,
        radius=ball_radius,
        color="blue",
        dynamic=True,
    )

    bar_thickness = 0.2
    plateau_top = (-5.0) + bottom * (10.0)
    plateau = Bar(
        left=(-5.0),
        right=(5.0),
        y=plateau_top - bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    vertical_bar_length = 0.1 * (10.0)
    left_bar = Bar(
        top=plateau.top + vertical_bar_length,
        bottom=plateau.top,
        x=green_ball_x + ball_radius,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_bar = Bar(
        top=plateau.top + vertical_bar_length,
        bottom=plateau.top,
        x=blue_ball_x - ball_radius,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    separator_length = (1.0 - bottom - 0.1) * (10.0)
    separator_x = left_bar.left + (right_bar.left - left_bar.left) / 2
    separator = Bar(
        top=(5.0),
        bottom=(5.0) - separator_length,
        x=separator_x,
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
        "green_ball": green_ball,
        "blue_ball": blue_ball,
        "plateau": plateau,
        "left_bar": left_bar,
        "right_bar": right_bar,
        "separator": separator,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00103",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
