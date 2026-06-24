"""task01000 — Basic.

A ball rests on a table; the player knocks it into a black static receptacle on
the floor. The receptacle is a three-bar bracket (floor + two walls). A purple
bar rests on the bracket floor as the contact target.
"""

import numpy as np

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Bar, Box, Bracket


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    table_w = rng.integers(100, 401)
    table_h = rng.integers(100, 401)
    ball_r = rng.integers(10, 31)
    ball_pos = rng.integers(ball_r + 5, table_w - ball_r - 4)
    goal_h = rng.integers(50, 201)
    goal_w = rng.integers(ball_r * 2 + 5, 600 - table_w - 29)
    goal_x = rng.integers(table_w + 10, 600 - goal_w - 9)
    flip = rng.integers(0, 2) == 1

    def ip(v):
        return v / 60 - 5

    def flip_x(x):
        return -x

    bracket_t = 0.175
    pad_t = bracket_t

    t_left, t_right = ip(0), ip(table_w)
    ball_cx = ip(ball_pos)
    ball_cy = ip(table_h) + ball_r / 60

    # goal_w is treated as interior width (follows PHYRE convention).
    goal_inner_w = goal_w / 60
    inner_cx = ip(goal_x) + goal_inner_w / 2
    bracket_y = ip(5)
    # Purple pad floats one bar-thickness above the bracket floor bar.
    pad_y = bracket_y + bracket_t * 2

    if flip:
        ball_cx = flip_x(ball_cx)
        t_left, t_right = flip_x(t_right), flip_x(t_left)
        inner_cx = flip_x(inner_cx)

    table = Box(
        left=t_left,
        right=t_right,
        top=ip(table_h),
        bottom=ip(0),
        dynamic=False,
        color="black",
    )
    ball = Ball(x=ball_cx, y=ball_cy, radius=ball_r / 60, color="green", dynamic=True)
    container = Bracket(
        x=inner_cx,
        y=bracket_y,
        width=goal_inner_w,
        height=goal_h / 60,
        thickness=bracket_t,
        dynamic=False,
        color="black",
    )
    purple_pad = Bar(
        left=inner_cx - goal_inner_w / 2,
        right=inner_cx + goal_inner_w / 2,
        y=pad_y,
        thickness=pad_t,
        dynamic=False,
        color="purple",
    )
    red_ball = Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "table": table,
        "ball": ball,
        "container": container,
        "purple_pad": purple_pad,
        "red_ball": red_ball,
    }
    return Level(
        name="task01000",
        objects=objects,
        action_objects=["red_ball"],
        success_condition=lambda engine: engine.is_in_contact_for_duration(
            "ball", "purple_pad", engine.config.default_success_time
        ),
    )
