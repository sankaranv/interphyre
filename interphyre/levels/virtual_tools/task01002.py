"""task01002 — Catapult.

An L-shaped (arm + fulcrum) catapult rests on a strut.  Dropping the action
ball on the long end launches the task ball into the container on the right.
"""

import numpy as np

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Bar, Box, Bracket


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    # VT-space geometry.
    cW = rng.integers(200, 401)
    cH = 20
    bR = rng.integers(5, 16)
    sW = rng.integers(10, 51)
    sH = rng.integers(60, 201)
    gW = rng.integers(60, 151)
    gH = rng.integers(60, 181)
    cT = rng.integers(5, 11)
    sp = rng.integers(25, 101)
    stP_raw = rng.integers(0, 151)
    stP = min(stP_raw, int(cW / 2))
    flip = rng.integers(0, 2) == 1

    cataCent = 600 - gW - sp - cW // 2
    cataLeft = cataCent - cW // 2

    def ip(v):
        return v / 60 - 5

    def flip_x(x):
        return -x

    strut = Box(
        left=ip(cataCent - sW // 2 + stP),
        right=ip(cataCent + sW // 2 + stP),
        top=ip(sH), bottom=ip(0),
        dynamic=False, color="black",
    )
    cradle = Box(
        left=ip(cataLeft), right=ip(cataLeft + 10),
        top=ip(sH), bottom=ip(0),
        dynamic=False, color="black",
    )

    wall_t = 7 / 60
    pad_t = wall_t
    goal_inner_w = (gW - 10) / 60
    goal_cx = ip(600 - gW) + goal_inner_w / 2 + wall_t
    bracket_y = ip(5)
    pad_y = bracket_y + wall_t * 2

    container = Bracket(
        x=goal_cx, y=bracket_y,
        width=goal_inner_w, height=gH / 60,
        thickness=wall_t, dynamic=False, color="black",
    )
    purple_pad = Bar(
        left=goal_cx - goal_inner_w / 2,
        right=goal_cx + goal_inner_w / 2,
        y=pad_y, thickness=pad_t,
        dynamic=False, color="purple",
    )

    arm_y = ip(sH + cT // 2)
    arm = Bar(
        left=ip(cataLeft), right=ip(cataLeft + cW),
        y=arm_y, thickness=cT / 60,
        dynamic=True, color="gray",
    )
    ball_x = ip(cataLeft + cT + bR + 30)
    ball_y = ip(sH + cT + bR)
    ball = Ball(x=ball_x, y=ball_y, radius=bR / 60, color="green", dynamic=True)

    if flip:
        strut = Box(
            left=flip_x(ip(cataCent + sW // 2 + stP)),
            right=flip_x(ip(cataCent - sW // 2 + stP)),
            top=ip(sH), bottom=ip(0),
            dynamic=False, color="black",
        )
        cradle = Box(
            left=flip_x(ip(cataLeft + 10)),
            right=flip_x(ip(cataLeft)),
            top=ip(sH), bottom=ip(0),
            dynamic=False, color="black",
        )
        fcx = flip_x(goal_cx)
        container = Bracket(
            x=fcx, y=bracket_y,
            width=goal_inner_w, height=gH / 60,
            thickness=wall_t, dynamic=False, color="black",
        )
        purple_pad = Bar(
            left=fcx - goal_inner_w / 2,
            right=fcx + goal_inner_w / 2,
            y=pad_y, thickness=pad_t,
            dynamic=False, color="purple",
        )
        arm = Bar(
            left=flip_x(ip(cataLeft + cW)), right=flip_x(ip(cataLeft)),
            y=arm_y, thickness=cT / 60,
            dynamic=True, color="gray",
        )
        ball = Ball(x=flip_x(ball_x), y=ball_y, radius=bR / 60, color="green", dynamic=True)

    red_ball = Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "strut": strut,
        "cradle": cradle,
        "container": container,
        "purple_pad": purple_pad,
        "arm": arm,
        "ball": ball,
        "red_ball": red_ball,
    }
    return Level(
        name="task01002",
        objects=objects,
        action_objects=["red_ball"],
        success_condition=lambda engine: engine.is_in_contact_for_duration(
            "ball", "purple_pad", engine.config.default_success_time
        ),
    )
