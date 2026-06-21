import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


def _bar_from_base(base_x, base_y, angle_deg, length, bar_thickness, color):
    angle_rad = np.radians(angle_deg)
    center_x = base_x + (length / 2) * np.cos(angle_rad)
    center_y = base_y + (length / 2) * np.sin(angle_rad)
    return Bar.from_point_and_angle(
        x=center_x,
        y=center_y,
        angle=angle_deg,
        length=length,
        thickness=bar_thickness,
        color=color,
        dynamic=False,
    )


def _create_cradle(center_x, center_y, left: bool):
    bar_thickness = 0.2
    cradle_angle = 30.0
    cradle_length = 0.22 * WORLD_WIDTH

    left_bar = _bar_from_base(
        center_x, center_y, 150.0, cradle_length, bar_thickness, "black"
    )
    right_bar = _bar_from_base(
        center_x, center_y, 30.0, cradle_length, bar_thickness, "black"
    )

    inner_angle = 18.0 if left else -18.0
    inner_base_x = center_x + (-0.04 if left else 0.04) * WORLD_WIDTH
    inner_base_y = center_y + 0.08 * WORLD_WIDTH
    inner_bar = _bar_from_base(
        inner_base_x,
        inner_base_y,
        inner_angle,
        0.2 * WORLD_WIDTH,
        bar_thickness,
        "gray",
    )

    ball_radius = 0.1 * WORLD_WIDTH / 2
    ball = Ball(
        x=inner_bar.right - ball_radius if left else inner_bar.left + ball_radius,
        y=inner_bar.top + ball_radius,
        radius=ball_radius,
        color="green" if left else "blue",
        dynamic=True,
    )

    top_bar = Bar(
        left=center_x - 0.08 * WORLD_WIDTH,
        right=center_x + 0.08 * WORLD_WIDTH,
        y=center_y + 0.25 * WORLD_WIDTH + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    return ball, left_bar, right_bar, inner_bar, top_bar


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    center_y = MIN_X + rng.choice(np.linspace(0.42, 0.5, 3)) * WORLD_WIDTH
    left_center_x = MIN_X + rng.choice(np.linspace(0.18, 0.28, 3)) * WORLD_WIDTH
    right_center_x = MIN_X + rng.choice(np.linspace(0.72, 0.82, 3)) * WORLD_WIDTH

    (
        green_ball,
        left_bar_1,
        right_bar_1,
        inner_bar_1,
        top_bar_1,
    ) = _create_cradle(left_center_x, center_y, left=True)
    (
        blue_ball,
        left_bar_2,
        right_bar_2,
        inner_bar_2,
        top_bar_2,
    ) = _create_cradle(
        right_center_x, center_y + 0.12 * WORLD_WIDTH, left=False
    )

    bar_thickness = 0.2
    base_length = 0.65 * WORLD_WIDTH
    base_left = Bar.from_point_and_angle(
        x=MIN_X + 0.15 * WORLD_WIDTH + base_length / 2,
        y=MIN_X + bar_thickness / 2,
        angle=-10.0,
        length=base_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    base_right = Bar.from_point_and_angle(
        x=MAX_X - 0.15 * WORLD_WIDTH - base_length / 2,
        y=MIN_X + bar_thickness / 2,
        angle=10.0,
        length=base_length,
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
        "left_bar_1": left_bar_1,
        "right_bar_1": right_bar_1,
        "inner_bar_1": inner_bar_1,
        "top_bar_1": top_bar_1,
        "left_bar_2": left_bar_2,
        "right_bar_2": right_bar_2,
        "inner_bar_2": inner_bar_2,
        "top_bar_2": top_bar_2,
        "base_left": base_left,
        "base_right": base_right,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00123",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
