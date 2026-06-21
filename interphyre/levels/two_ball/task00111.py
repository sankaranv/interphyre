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

    dist_options = np.linspace(0.05, 0.15, 3)
    size_options = np.linspace(0.6, 0.8, 4)
    height_options = np.linspace(0.0, 0.3, 6)

    while True:
        size = rng.choice(size_options)
        left_d = rng.choice(dist_options)
        right_d = rng.choice(dist_options)
        if size == 0.8 and (left_d + right_d) >= 0.2:
            continue
        ground_y = rng.choice(height_options)
        break

    bar_thickness = 0.2
    ground_bottom = MIN_X + ground_y * WORLD_WIDTH
    ground = Bar(
        left=MIN_X,
        right=MAX_X,
        y=ground_bottom + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    stick_length = size * WORLD_WIDTH
    stick_bottom = ground.top
    stick_top = stick_bottom + stick_length
    left_stick_x = MIN_X + left_d * WORLD_WIDTH
    right_stick_x = MAX_X - right_d * WORLD_WIDTH
    left_stick = Bar(
        top=stick_top,
        bottom=stick_bottom,
        x=left_stick_x,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )
    right_stick = Bar(
        top=stick_top,
        bottom=stick_bottom,
        x=right_stick_x,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )

    ball_radius = 0.1 * WORLD_WIDTH / 2
    green_ball = Ball(
        x=left_stick_x + 0.4,
        y=stick_top + ball_radius,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )
    blue_ball = Ball(
        x=right_stick_x - 0.4,
        y=stick_top + ball_radius,
        radius=ball_radius,
        color="blue",
        dynamic=True,
    )

    slope_scale = (
        0.25 / ((left_d + right_d) / 0.2) if (left_d + right_d) > 0.2 else 0.3
    )
    slope_length = slope_scale * WORLD_WIDTH
    slope_left = Bar.from_point_and_angle(
        x=left_stick.right + slope_length / 2,
        y=stick_top - 0.4,
        angle=-10,
        length=slope_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    slope_right = Bar.from_point_and_angle(
        x=right_stick.left - slope_length / 2,
        y=stick_top - 0.4,
        angle=10,
        length=slope_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    base_slope_length = 0.25 * WORLD_WIDTH
    base_left = Bar.from_point_and_angle(
        x=left_stick.x - 0.5,
        y=ground.top + bar_thickness / 2,
        angle=30,
        length=base_slope_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    base_right = Bar.from_point_and_angle(
        x=right_stick.x + 0.5,
        y=ground.top + bar_thickness / 2,
        angle=-30,
        length=base_slope_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    border_y = blue_ball.y + blue_ball.radius + bar_thickness / 2 + 0.2
    border = Bar(
        left=MIN_X,
        right=MAX_X,
        y=border_y,
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
        "ground": ground,
        "left_stick": left_stick,
        "right_stick": right_stick,
        "slope_left": slope_left,
        "slope_right": slope_right,
        "base_left": base_left,
        "base_right": base_right,
        "border": border,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00111",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
