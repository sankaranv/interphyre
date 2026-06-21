import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.levels.two_ball._constants import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_ground", success_time
    )


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    ball_sizes = [0.1, 0.15, 0.2]
    hole_sizes = [0.11, 0.16, 0.21]
    hole_lefts = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    bar_heights = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]

    bar_thickness = 0.2
    green_ball_x = 0.0
    ball_top = MIN_Y + 0.95 * WORLD_HEIGHT

    while True:
        ball_size = rng.choice(ball_sizes)
        hole_size = rng.choice(hole_sizes)
        hole_left = rng.choice(hole_lefts)
        bar_height = rng.choice(bar_heights)
        bottom_bar_height = bar_height - ball_size * 2
        hole_right = hole_left + hole_size
        if ball_size > hole_size:
            continue
        if not 0.0 < hole_left < 1.0 or not 0.0 < hole_right < 1.0:
            continue
        if bottom_bar_height <= 0:
            continue

        ball_radius = ball_size * WORLD_WIDTH / 2
        hole_left_x = MIN_X + hole_left * WORLD_WIDTH
        hole_right_x = MIN_X + hole_right * WORLD_WIDTH
        top_bar_bottom = MIN_Y + bar_height * WORLD_HEIGHT
        top_bar_top = top_bar_bottom + bar_thickness
        ball_left = green_ball_x - ball_radius
        ball_right = green_ball_x + ball_radius
        ball_bottom = ball_top - 2 * ball_radius

        if ball_left >= hole_left_x and ball_right <= hole_right_x:
            continue
        if ball_bottom <= top_bar_top:
            continue

        bottom_hole_left = hole_left + (0.15 if hole_left < 0.5 else -0.15)
        bottom_hole_right = bottom_hole_left + hole_size
        if (
            not 0.0 < bottom_hole_left < 1.0
            or not 0.0 < bottom_hole_right < 1.0
        ):
            continue
        break

    ball_radius = ball_size * WORLD_WIDTH / 2
    green_ball_y = ball_top - ball_radius
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    top_bar_bottom = MIN_Y + bar_height * WORLD_HEIGHT
    top_bar_y = top_bar_bottom + bar_thickness / 2
    hole_left_x = MIN_X + hole_left * WORLD_WIDTH
    hole_right_x = MIN_X + (hole_left + hole_size) * WORLD_WIDTH

    left_top_bar = Bar(
        left=MIN_X,
        right=hole_left_x,
        y=top_bar_y,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_top_bar = Bar(
        left=hole_right_x,
        right=MAX_X,
        y=top_bar_y,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    shift = 0.15 if hole_left < 0.5 else -0.15
    bottom_bar_bottom = MIN_Y + bottom_bar_height * WORLD_HEIGHT
    bottom_bar_y = bottom_bar_bottom + bar_thickness / 2
    bottom_hole_left = hole_left + shift
    bottom_hole_right = bottom_hole_left + hole_size
    bottom_hole_left_x = MIN_X + bottom_hole_left * WORLD_WIDTH
    bottom_hole_right_x = MIN_X + bottom_hole_right * WORLD_WIDTH

    left_bottom_bar = Bar(
        left=MIN_X,
        right=bottom_hole_left_x,
        y=bottom_bar_y,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_bottom_bar = Bar(
        left=bottom_hole_right_x,
        right=MAX_X,
        y=bottom_bar_y,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    if left_bottom_bar.bottom <= ball_radius:
        left_bottom_bar.y = ball_radius + bar_thickness / 2 + 0.1
        right_bottom_bar.y = left_bottom_bar.y

    obstacle_height = 0.02 * WORLD_HEIGHT
    left_obstacle = Bar(
        top=left_bottom_bar.top + obstacle_height,
        bottom=left_bottom_bar.top,
        x=left_bottom_bar.right,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_obstacle = Bar(
        top=right_bottom_bar.top + obstacle_height,
        bottom=right_bottom_bar.top,
        x=right_bottom_bar.left,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    purple_ground = Bar(
        left=MIN_X,
        right=MAX_X,
        y=MIN_Y + bar_thickness / 2,
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
        "left_top_bar": left_top_bar,
        "right_top_bar": right_top_bar,
        "left_bottom_bar": left_bottom_bar,
        "right_bottom_bar": right_bottom_bar,
        "left_obstacle": left_obstacle,
        "right_obstacle": right_obstacle,
        "purple_ground": purple_ground,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00102",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Drop the green ball through the holes."},
    )
