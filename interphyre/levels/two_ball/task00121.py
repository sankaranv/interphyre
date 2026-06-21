import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


def _create_structure(ball_x, ball_y, left: bool):
    bar_thickness = 0.2
    ball_radius = 0.1 * WORLD_WIDTH / 2
    ball = Ball(
        x=MIN_X + ball_x * WORLD_WIDTH,
        y=MIN_X + ball_y * WORLD_WIDTH,
        radius=ball_radius,
        color="green" if left else "blue",
        dynamic=True,
    )

    bottom_bar_length = 0.2 * WORLD_WIDTH
    bottom_bar = Bar(
        left=ball.x - bottom_bar_length / 2,
        right=ball.x + bottom_bar_length / 2,
        y=ball.y - ball_radius - bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    top_bar_length = 0.1 * WORLD_WIDTH
    top_bar = Bar(
        left=ball.x - top_bar_length / 2,
        right=ball.x + top_bar_length / 2,
        y=ball.y + ball_radius + 0.01 * WORLD_WIDTH + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    if left:
        bottom_bar.x = ball.x + (bottom_bar_length / 2 - ball_radius)
        top_bar.x = ball.x + (top_bar_length / 2 - ball_radius)
    else:
        bottom_bar.x = ball.x - (bottom_bar_length / 2 - ball_radius)
        top_bar.x = ball.x - (top_bar_length / 2 - ball_radius)

    stick_length = 0.12 * WORLD_WIDTH
    stick_bottom = bottom_bar.top
    stick_top = stick_bottom + stick_length
    stick_x = bottom_bar.left if left else bottom_bar.right
    stick = Bar(
        top=stick_top,
        bottom=stick_bottom,
        x=stick_x,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )

    vertical_bar = Bar(
        top=MIN_X + WORLD_WIDTH,
        bottom=bottom_bar.top,
        x=bottom_bar.right if left else bottom_bar.left,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    vertical_bar_2_length = 0.1 * WORLD_WIDTH
    vertical_bar_2_bottom = stick.top + 0.2 * WORLD_WIDTH
    vertical_bar_2 = Bar(
        top=vertical_bar_2_bottom + vertical_bar_2_length,
        bottom=vertical_bar_2_bottom,
        x=stick.left if left else stick.right,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    return ball, vertical_bar, bottom_bar, top_bar, stick, vertical_bar_2


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    ball_x_options = [0.1 * val for val in range(2, 8)]
    ball_y_options = [0.1 * val for val in range(2, 8)]

    while True:
        ball1_x = rng.choice(ball_x_options)
        ball2_x = rng.choice(ball_x_options)
        ball1_y = rng.choice(ball_y_options)
        ball2_y = rng.choice(ball_y_options)
        if ball2_x - ball1_x < 0.3:
            continue
        break

    (
        green_ball,
        vertical_bar_1,
        bottom_bar_1,
        top_bar_1,
        stick_1,
        vertical_bar_1b,
    ) = _create_structure(ball1_x, ball1_y, left=True)
    (
        blue_ball,
        vertical_bar_2,
        bottom_bar_2,
        top_bar_2,
        stick_2,
        vertical_bar_2b,
    ) = _create_structure(ball2_x, ball2_y, left=False)

    bar_thickness = 0.2
    ramp_scale = (vertical_bar_2.left - vertical_bar_1.right) / (2.0 * WORLD_WIDTH)
    ramp_length = ramp_scale * WORLD_WIDTH
    ramp_y = MIN_X - 0.015 * WORLD_WIDTH + bar_thickness / 2
    left_ramp = Bar.from_point_and_angle(
        x=vertical_bar_1.left + ramp_length / 2,
        y=ramp_y,
        angle=-10.0,
        length=ramp_length,
        thickness=0.2,
        color="black",
        dynamic=False,
    )
    right_ramp = Bar.from_point_and_angle(
        x=vertical_bar_2.right - ramp_length / 2,
        y=ramp_y,
        angle=10.0,
        length=ramp_length,
        thickness=0.2,
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
        "vertical_bar_1": vertical_bar_1,
        "vertical_bar_2": vertical_bar_2,
        "bottom_bar_1": bottom_bar_1,
        "bottom_bar_2": bottom_bar_2,
        "top_bar_1": top_bar_1,
        "top_bar_2": top_bar_2,
        "stick_1": stick_1,
        "stick_2": stick_2,
        "vertical_bar_1b": vertical_bar_1b,
        "vertical_bar_2b": vertical_bar_2b,
        "left_ramp": left_ramp,
        "right_ramp": right_ramp,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00121",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
