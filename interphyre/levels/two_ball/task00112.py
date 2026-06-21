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

    num_bars_options = range(5, 9)
    bar_y_options = np.linspace(0.4, 0.8, 10)
    ball_x_options = np.linspace(0.1, 0.4, 10)
    left = rng.choice([True, False])

    num_bars = rng.choice(list(num_bars_options))
    bar_y = rng.choice(bar_y_options)
    ball_x = rng.choice(ball_x_options)

    bar_thickness = 0.2
    purple_ground = Bar(
        left=(-5.0),
        right=(5.0),
        y=(-5.0) + bar_thickness / 2,
        thickness=bar_thickness,
        color="purple",
        dynamic=False,
    )

    multiplier = 0.1
    offset = 0.2
    if not left:
        multiplier = -multiplier
        offset = 1.0 - offset

    bars = []
    for idx in range(num_bars):
        bar_scale = 0.15 + 0.05 * idx
        bar_length = bar_scale * (10.0)
        bar_left = (-5.0) + (offset + multiplier * idx) * (10.0)
        bar = Bar(
            top=purple_ground.top + bar_length,
            bottom=purple_ground.top,
            x=bar_left + bar_length / 2,
            thickness=bar_thickness,
            color="gray",
            dynamic=True,
        )
        bars.append(bar)

    obstacle_length = 0.7 * (10.0)
    obstacle_y = (-5.0) + bar_y * (10.0)
    if left:
        obstacle = Bar(
            left=(5.0) - obstacle_length,
            right=(5.0),
            y=obstacle_y + bar_thickness / 2,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )
    else:
        obstacle = Bar(
            left=(-5.0),
            right=(-5.0) + obstacle_length,
            y=obstacle_y + bar_thickness / 2,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )

    ball_radius = 0.1 * (10.0) / 2
    ball1_x = (1.0 - ball_x if left else ball_x) * (10.0) + (-5.0)
    ball1_y = (-5.0) + 0.9 * (10.0) + ball_radius
    green_ball = Ball(
        x=ball1_x,
        y=ball1_y,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    last_bar = bars[-1]
    ball2_y = last_bar.top + (obstacle.bottom - last_bar.top) / 2
    if left:
        ball2_x = last_bar.left + ball_radius
    else:
        ball2_x = last_bar.right - ball_radius
    blue_ball = Ball(
        x=ball2_x,
        y=ball2_y,
        radius=ball_radius,
        color="gray",
        dynamic=True,
    )

    blue_ball_bottom = blue_ball.y - ball_radius
    blue_ball_top = blue_ball.y + ball_radius
    if blue_ball_bottom <= last_bar.top or blue_ball_top >= obstacle.bottom:
        blue_ball.y = last_bar.top + ball_radius + 0.1

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
        "purple_ground": purple_ground,
        "obstacle": obstacle,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }
    for idx, bar in enumerate(bars):
        objects[f"bar_{idx}"] = bar

    return Level(
        name="task00112",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball to the purple ground."},
    )
