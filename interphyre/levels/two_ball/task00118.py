import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "purple_wall", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    lever_angle_options = np.linspace(10.0, 20.0, 3)
    lever_x_options = np.linspace(0.25, 0.45, 3)
    lever_y_options = np.linspace(0.1, 0.2, 3)
    top_bar_y_options = np.linspace(0.75, 0.85, 3)
    top_bar_angle_options = np.linspace(-15.0, -5.0, 3)

    lever_angle = rng.choice(lever_angle_options)
    lever_x = rng.choice(lever_x_options)
    lever_y = rng.choice(lever_y_options)
    top_bar_y = rng.choice(top_bar_y_options)
    top_bar_angle = rng.choice(top_bar_angle_options)

    bar_thickness = 0.2
    lever_length = 0.45 * WORLD_WIDTH
    lever = Bar.from_point_and_angle(
        x=MIN_X + lever_x * WORLD_WIDTH,
        y=MIN_X + lever_y * WORLD_WIDTH + bar_thickness / 2,
        angle=lever_angle,
        length=lever_length,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )

    fulcrum_radius = 0.08 * WORLD_WIDTH / 2
    fulcrum = Ball(
        x=lever.left + 0.1 * WORLD_WIDTH,
        y=lever.bottom - fulcrum_radius,
        radius=fulcrum_radius,
        color="black",
        dynamic=False,
    )

    ball_radius = 0.07 * WORLD_WIDTH / 2
    green_ball = Ball(
        x=lever.right - ball_radius,
        y=lever.top + ball_radius,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    top_bar = Bar.from_point_and_angle(
        x=MAX_X - 0.15 * WORLD_WIDTH,
        y=MIN_X + top_bar_y * WORLD_WIDTH,
        angle=top_bar_angle,
        length=0.35 * WORLD_WIDTH,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    purple_wall = Bar(
        top=MAX_X,
        bottom=MIN_X,
        x=MAX_X,
        thickness=bar_thickness,
        color="purple",
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
        "fulcrum": fulcrum,
        "lever": lever,
        "top_bar": top_bar,
        "purple_wall": purple_wall,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00118",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
