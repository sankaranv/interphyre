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

    step_size = 0.1
    platform_x_options = [step_size * val for val in range(1, 9)]
    platform_y_options = [step_size * val for val in range(4, 8)]

    while True:
        platform1_x = rng.choice(platform_x_options)
        platform2_x = rng.choice(platform_x_options)
        platform1_y = rng.choice(platform_y_options)
        platform2_y = rng.choice(platform_y_options)
        if platform2_x - platform1_x <= 2.5 * step_size:
            continue
        break

    bar_thickness = 0.2
    platform_length = 0.1 * (10.0)
    platform1_left = (-5.0) + platform1_x * (10.0)
    platform1_bottom = (-5.0) + platform1_y * (10.0)
    platform1 = Bar(
        left=platform1_left,
        right=platform1_left + platform_length,
        y=platform1_bottom + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    platform2_left = (-5.0) + platform2_x * (10.0)
    platform2_bottom = (-5.0) + platform2_y * (10.0)
    platform2 = Bar(
        left=platform2_left,
        right=platform2_left + platform_length,
        y=platform2_bottom + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    ball_radius = 0.1 * (10.0) / 2
    green_ball_x = (platform1.left + platform1.right) / 2
    green_ball_y = platform1.top + ball_radius
    blue_ball_x = (platform2.left + platform2.right) / 2
    blue_ball_y = platform2.top + ball_radius
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

    sep_length = (1.0 - min(platform1_y, platform2_y)) * (10.0)
    sep_x = platform1.right + (platform2.left - platform1.right) / 2
    separator = Bar(
        top=(5.0),
        bottom=(5.0) - sep_length,
        x=sep_x,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    floor_length = 0.6 * (10.0)
    left_floor = Bar.from_point_and_angle(
        x=(-5.0) + 0.2 * (10.0) + floor_length / 2,
        y=(-5.0) + bar_thickness / 2,
        length=floor_length,
        angle=-5.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_floor = Bar.from_point_and_angle(
        x=(5.0) - 0.2 * (10.0) - floor_length / 2,
        y=(-5.0) + bar_thickness / 2,
        length=floor_length,
        angle=5.0,
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
        "platform_1": platform1,
        "platform_2": platform2,
        "separator": separator,
        "left_floor": left_floor,
        "right_floor": right_floor,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00110",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
