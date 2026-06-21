import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    ball_x_options = np.linspace(0.15, 0.9, 8)
    bar_y_options = [0.3, 0.4, 0.5, 0.6]
    obstacle_width_options = np.linspace(0.1, 0.4, 6)

    while True:
        ball1_x = rng.choice(ball_x_options)
        ball2_x = rng.choice(ball_x_options)
        if ball2_x > ball1_x:
            break

    bar_y = rng.choice(bar_y_options)
    obstacle_width = rng.choice(obstacle_width_options)

    ball_radius = 0.1 * WORLD_WIDTH / 2
    green_ball_x = MIN_X + ball1_x * WORLD_WIDTH
    blue_ball_x = MIN_X + ball2_x * WORLD_WIDTH
    green_ball = Ball(
        x=green_ball_x,
        y=MIN_X + 0.9 * WORLD_WIDTH + ball_radius,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )
    blue_ball = Ball(
        x=blue_ball_x,
        y=MIN_X + 0.9 * WORLD_WIDTH + ball_radius,
        radius=ball_radius,
        color="blue",
        dynamic=True,
    )

    bar_thickness = 0.2
    bar_scale = 1.0 - ((blue_ball_x - ball_radius - MIN_X) / WORLD_WIDTH)
    bar1_length = bar_scale * WORLD_WIDTH
    bar1 = Bar(
        left=MAX_X - bar1_length,
        right=MAX_X,
        y=MIN_X + bar_y * WORLD_WIDTH + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    bar2_length = (bar_scale + obstacle_width) * WORLD_WIDTH
    bar2 = Bar(
        left=MAX_X - bar2_length,
        right=MAX_X,
        y=MIN_X + (bar_y - 0.4 * obstacle_width) * WORLD_WIDTH + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    vertical_length = (bar1.top - bar2.top) + 0.04 * WORLD_WIDTH
    vertical_bar = Bar(
        top=bar2.top + vertical_length,
        bottom=bar2.top,
        x=bar1.left,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    top_vertical_top = vertical_bar.top - 0.05 * WORLD_WIDTH
    top_vertical = Bar(
        top=top_vertical_top,
        bottom=top_vertical_top - WORLD_WIDTH,
        x=bar2.left,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    block_bar = Bar(
        top=bar1.top + WORLD_WIDTH,
        bottom=bar1.top,
        x=blue_ball_x + ball_radius + 0.02 * WORLD_WIDTH,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    ramp_scale = bar2.left - MIN_X
    ramp_length = ramp_scale / 1.9
    left_ramp = Bar.from_point_and_angle(
        x=MIN_X + ramp_length / 2,
        y=MIN_X + bar_thickness / 2,
        angle=-10.0,
        length=ramp_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_ramp = Bar.from_point_and_angle(
        x=bar2.left - ramp_length / 2,
        y=MIN_X + bar_thickness / 2,
        angle=10.0,
        length=ramp_length,
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
        "bar_1": bar1,
        "bar_2": bar2,
        "vertical_bar": vertical_bar,
        "top_vertical": top_vertical,
        "block_bar": block_bar,
        "left_ramp": left_ramp,
        "right_ramp": right_ramp,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00114",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
