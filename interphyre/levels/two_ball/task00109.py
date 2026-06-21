import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_ground", success_time
    )


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    bar_thickness = 0.2
    top_bar_x_options = np.linspace(0.15, 0.35, 5)
    top_bar_y_options = np.linspace(0.7, 0.85, 4)
    top_bar_angle_options = np.linspace(-25.0, -15.0, 3)
    mid_y_options = np.linspace(0.45, 0.55, 3)
    mid_angle_options = np.linspace(20.0, 30.0, 3)
    post_x_options = np.linspace(0.2, 0.5, 4)
    post_height_options = np.linspace(0.25, 0.45, 3)
    ball_size_options = np.linspace(0.05, 0.08, 3)

    top_bar_x = rng.choice(top_bar_x_options)
    top_bar_y = rng.choice(top_bar_y_options)
    top_bar_angle = rng.choice(top_bar_angle_options)
    mid_y = rng.choice(mid_y_options)
    mid_angle = rng.choice(mid_angle_options)
    post_x = rng.choice(post_x_options)
    post_height = rng.choice(post_height_options)
    ball_size = rng.choice(ball_size_options)

    top_bar_length = 0.35 * (10.0)
    top_bar = Bar.from_point_and_angle(
        x=(-5.0) + top_bar_x * (10.0),
        y=(-5.0) + top_bar_y * (10.0),
        length=top_bar_length,
        angle=top_bar_angle,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    mid_length = 0.3 * (10.0)
    mid_center_x = (-5.0) + 0.55 * (10.0)
    left_mid = Bar.from_point_and_angle(
        x=mid_center_x - 0.18 * (10.0),
        y=(-5.0) + mid_y * (10.0),
        length=mid_length,
        angle=mid_angle,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_mid = Bar.from_point_and_angle(
        x=mid_center_x + 0.18 * (10.0),
        y=(-5.0) + mid_y * (10.0),
        length=mid_length,
        angle=-mid_angle,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    post = Bar(
        top=(-5.0) + post_height * (10.0),
        bottom=(-5.0),
        x=(-5.0) + post_x * (10.0),
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    ball_radius = ball_size * (10.0) / 2
    green_ball = Ball(
        x=top_bar.left + ball_radius,
        y=top_bar.top + ball_radius,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    purple_ground = Bar(
        left=(-5.0),
        right=(5.0),
        y=(-5.0) + bar_thickness / 2,
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
        "top_bar": top_bar,
        "left_mid": left_mid,
        "right_mid": right_mid,
        "post": post,
        "purple_ground": purple_ground,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00109",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball onto the purple ground."},
    )
