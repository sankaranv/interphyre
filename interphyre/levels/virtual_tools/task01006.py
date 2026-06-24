"""task01006 — Unbox.

Ball on a slope rolls into a container whose opening is blocked by a dynamic
lid.  The player must knock the lid off so the ball can enter.
"""

import numpy as np

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Bar, Box, Bracket, Wedge


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    sL = rng.integers(200, 401)
    sR = rng.integers(100, 191)
    sW = rng.integers(100, 301)
    bpos_x = rng.integers(30, 101)
    bpos_y_offset = rng.integers(15, 51)
    bpos_y = sL + bpos_y_offset
    goal_w = rng.integers(80, 151)
    lid_extent = rng.integers(10, 51)
    lid_t = rng.integers(8, 21)
    goal_h = rng.integers(60, sR)
    flip = rng.integers(0, 2) == 1

    def ip(v):
        return v / 60 - 5

    def flip_x(x):
        return -x

    slope = Wedge(
        x1=ip(0), y1=ip(sL),
        x2=ip(sW), y2=ip(sR),
        bottom=ip(0),
        dynamic=False, color="black",
    )

    goal_L = sW
    goal_R = sW + goal_w
    wall_t = 7 / 60
    pad_t = wall_t
    goal_inner_w = goal_w / 60 - 2 * wall_t
    goal_cx = ip(goal_L) + wall_t + goal_inner_w / 2
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

    lid = Box(
        left=ip(goal_L), right=ip(goal_R + lid_extent),
        top=ip(goal_h + 5 + lid_t), bottom=ip(goal_h + 5),
        dynamic=True, color="gray",
    )
    ball = Ball(x=ip(bpos_x), y=ip(bpos_y), radius=15 / 60, color="green", dynamic=True)

    if flip:
        slope = Wedge(
            x1=flip_x(ip(sW)), y1=ip(sR),
            x2=flip_x(ip(0)), y2=ip(sL),
            bottom=ip(0),
            dynamic=False, color="black",
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
        lid = Box(
            left=flip_x(ip(goal_R + lid_extent)), right=flip_x(ip(goal_L)),
            top=ip(goal_h + 5 + lid_t), bottom=ip(goal_h + 5),
            dynamic=True, color="gray",
        )
        ball = Ball(x=flip_x(ip(bpos_x)), y=ip(bpos_y), radius=15 / 60, color="green", dynamic=True)

    red_ball = Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "slope": slope,
        "container": container,
        "purple_pad": purple_pad,
        "lid": lid,
        "ball": ball,
        "red_ball": red_ball,
    }
    return Level(
        name="task01006",
        objects=objects,
        action_objects=["red_ball"],
        success_condition=lambda engine: engine.is_in_contact_for_duration(
            "ball", "purple_pad", engine.config.default_success_time
        ),
    )
