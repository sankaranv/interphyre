"""task01005 — LaunchA.

Ball on a table with a small slope ramp at one edge and a ceiling cover above
it.  The player must fire the ball past the cover so it lands in a container
on the other side of the table.
"""

import numpy as np

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Bar, Box, Bracket, Wedge


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    table_w = rng.integers(300, 401)
    table_h = rng.integers(100, 401)
    ball_r = rng.integers(10, 31)
    goal_h = rng.integers(50, 201)
    sL = rng.integers(20, 101)
    sW = rng.integers(10, 51)
    ball_pos = rng.integers(ball_r + 5 + sW, table_w - ball_r - 4)
    cover_L = rng.integers(ball_pos - ball_r * 3, ball_pos - ball_r)
    cover_R = rng.integers(ball_pos + ball_r, ball_pos + ball_r * 3)
    cover_Y_min = ball_r * 2 + table_h
    cover_Y_max = min(ball_r * 5 + table_h, 585)
    cover_Y = rng.integers(cover_Y_min, max(cover_Y_min + 1, cover_Y_max))
    goal_w = rng.integers(ball_r * 2 + 5, 600 - table_w - 29)
    goal_x = rng.integers(table_w + 10, 600 - goal_w - 9)
    flip = rng.integers(0, 2) == 1

    def ip(v):
        return v / 60 - 5

    def flip_x(x):
        return -x

    table = Box(
        left=ip(0), right=ip(table_w),
        top=ip(table_h), bottom=ip(0),
        dynamic=False, color="black",
    )
    slope = Wedge(
        x1=ip(0), y1=ip(sL + table_h),
        x2=ip(sW), y2=ip(table_h),
        bottom=ip(table_h),
        dynamic=False, color="black",
    )
    cover = Box(
        left=ip(cover_L), right=ip(cover_R),
        top=ip(cover_Y + 15), bottom=ip(cover_Y),
        dynamic=False, color="black",
    )
    ball = Ball(
        x=ip(ball_pos), y=ip(table_h) + ball_r / 60,
        radius=ball_r / 60, color="green", dynamic=True,
    )

    wall_t = 7 / 60
    pad_t = wall_t
    goal_inner_w = (goal_w - 10) / 60
    goal_cx = ip(goal_x) + wall_t + goal_inner_w / 2
    bracket_y = ip(5)
    pad_y = bracket_y + wall_t * 2

    container = Bracket(
        x=goal_cx, y=bracket_y,
        width=goal_inner_w, height=goal_h / 60,
        thickness=wall_t, dynamic=False, color="black",
    )
    purple_pad = Bar(
        left=goal_cx - goal_inner_w / 2,
        right=goal_cx + goal_inner_w / 2,
        y=pad_y, thickness=pad_t,
        dynamic=False, color="purple",
    )

    if flip:
        table = Box(
            left=flip_x(ip(table_w)), right=flip_x(ip(0)),
            top=ip(table_h), bottom=ip(0),
            dynamic=False, color="black",
        )
        slope = Wedge(
            x1=flip_x(ip(sW)), y1=ip(table_h),
            x2=flip_x(ip(0)), y2=ip(sL + table_h),
            bottom=ip(table_h),
            dynamic=False, color="black",
        )
        cover = Box(
            left=flip_x(ip(cover_R)), right=flip_x(ip(cover_L)),
            top=ip(cover_Y + 15), bottom=ip(cover_Y),
            dynamic=False, color="black",
        )
        ball = Ball(
            x=flip_x(ip(ball_pos)), y=ip(table_h) + ball_r / 60,
            radius=ball_r / 60, color="green", dynamic=True,
        )
        fcx = flip_x(goal_cx)
        container = Bracket(
            x=fcx, y=bracket_y,
            width=goal_inner_w, height=goal_h / 60,
            thickness=wall_t, dynamic=False, color="black",
        )
        purple_pad = Bar(
            left=fcx - goal_inner_w / 2,
            right=fcx + goal_inner_w / 2,
            y=pad_y, thickness=pad_t,
            dynamic=False, color="purple",
        )

    red_ball = Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "table": table,
        "slope": slope,
        "cover": cover,
        "ball": ball,
        "container": container,
        "purple_pad": purple_pad,
        "red_ball": red_ball,
    }
    return Level(
        name="low_bridge",
        objects=objects,
        action_objects=["red_ball"],
        success_condition=lambda engine: engine.is_in_contact_for_duration(
            "ball", "purple_pad", engine.config.default_success_time
        ),
    )
