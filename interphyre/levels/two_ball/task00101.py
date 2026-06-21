import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.levels.two_ball._constants import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    dist_to_obstacle = 0.2
    horizontal_options = [0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
    vertical_options = [0.2, 0.3, 0.4]
    base_x_options = [0.1, 0.2, 0.3, 0.4]
    base_y_options = [0.3, 0.4, 0.5]

    while True:
        horizontal_dist = rng.choice(horizontal_options)
        vertical_dist = rng.choice(vertical_options)
        if horizontal_dist + 0.1 > vertical_dist:
            break
    base_x = rng.choice(base_x_options)
    base_y = rng.choice(base_y_options)

    ball_radius = 0.1 * WORLD_WIDTH / 2
    green_ball_x = MIN_X + base_x * WORLD_WIDTH
    green_ball_y = MIN_Y + base_y * WORLD_HEIGHT + ball_radius
    blue_ball_x = MIN_X + (base_x + horizontal_dist) * WORLD_WIDTH
    blue_ball_y = MIN_Y + (base_y + vertical_dist) * WORLD_HEIGHT + ball_radius

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
    obstacle_offset = dist_to_obstacle * WORLD_WIDTH
    left_bar = Bar(
        left=green_ball_x - ball_radius,
        right=green_ball_x + ball_radius,
        y=green_ball_y - ball_radius - obstacle_offset + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_bar = Bar(
        left=blue_ball_x - ball_radius,
        right=blue_ball_x + ball_radius,
        y=blue_ball_y - ball_radius - obstacle_offset + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    vertical_bar_length = 1.0 * WORLD_HEIGHT
    left_vertical_top = left_bar.y - bar_thickness / 2
    right_vertical_top = right_bar.y - bar_thickness / 2
    left_vertical = Bar(
        top=left_vertical_top,
        bottom=left_vertical_top - vertical_bar_length,
        x=left_bar.x,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_vertical = Bar(
        top=right_vertical_top,
        bottom=right_vertical_top - vertical_bar_length,
        x=right_bar.x,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    ramp_length = horizontal_dist * WORLD_WIDTH / 2
    ramp_y = MIN_Y + bar_thickness / 2
    left_ramp = Bar.from_point_and_angle(
        x=left_vertical.right + ramp_length / 2,
        y=ramp_y,
        angle=-10,
        length=ramp_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_ramp = Bar.from_point_and_angle(
        x=right_vertical.left - ramp_length / 2,
        y=ramp_y,
        angle=10,
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
        "left_bar": left_bar,
        "right_bar": right_bar,
        "left_vertical": left_vertical,
        "right_vertical": right_vertical,
        "left_ramp": left_ramp,
        "right_ramp": right_ramp,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00101",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
