"""task01000 — Basic.

A ball rests on a table; the player must knock it into a container sitting on
the floor to the right (or left, when flip_lr=True).
"""

import numpy as np

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Basket, Box


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    # Randomise geometry in VT pixel space (600×600).
    table_w = rng.integers(100, 401)       # VT pixels
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

    t_left, t_right = ip(0), ip(table_w)
    t_bottom, t_top = ip(0), ip(table_h)

    ball_cx = ip(ball_pos)
    ball_cy = ip(table_h) + ball_r / 60

    wall_t = 7 / 60
    goal_inner_w = goal_w / 60
    goal_cx = ip(goal_x) + goal_w / 120  # interior center

    if flip:
        ball_cx = flip_x(ball_cx)
        t_left, t_right = flip_x(t_right), flip_x(t_left)
        goal_cx = flip_x(goal_cx)

    table = Box(left=t_left, right=t_right, top=t_top, bottom=t_bottom, dynamic=False, color="black")
    ball = Ball(x=ball_cx, y=ball_cy, radius=ball_r / 60, color="green", dynamic=True)
    container = Basket(
        x=goal_cx,
        y=ip(5),
        bottom_width=goal_inner_w,
        top_width=goal_inner_w,
        height=goal_h / 60,
        wall_thickness=wall_t,
        floor_thickness=wall_t,
        anchor="bottom_center",
        enable_sensor=False,
        dynamic=False,
        color="purple",
    )

    # Action: one red ball dropped from above.
    red_ball = Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "table": table,
        "ball": ball,
        "container": container,
        "red_ball": red_ball,
    }
    return Level(
        name="task01000",
        objects=objects,
        action_objects=["red_ball"],
        success_condition=lambda engine: engine.is_in_contact_for_duration(
            "ball", "container", engine.config.default_success_time
        ),
    )
