"""task01007 — Remove.

A ball rests on an elevated slope.  A blocking ball sits on a platform above
the container, preventing the task ball from entering.  The player must
remove the blocking ball.
"""

import numpy as np

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Bar, Box, Bracket, Wedge


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    gW = rng.integers(100, 201)
    gH = rng.integers(80, 101)
    bR = rng.integers(7, 13)
    sL = rng.integers(40, 71)
    sR = rng.integers(5, 11)
    sW = rng.integers(200, 276)
    sH = rng.integers(380, 451)
    pL = rng.integers(300, 401)
    pR = rng.integers(475, 501)
    pH = rng.integers(200, 251)
    bS = rng.integers(30, 41)
    pWidth = 15
    jitter = rng.integers(0, pR - pL)
    flip = rng.integers(0, 2) == 1

    def ip(v):
        return v / 60 - 5

    def flip_x(x):
        return -x

    slope = Wedge(
        x1=ip(0), y1=ip(sH + sL),
        x2=ip(sW), y2=ip(sH + sR),
        bottom=ip(sH),
        dynamic=False, color="black",
    )
    platform = Box(
        left=ip(pL), right=ip(pR),
        top=ip(pH + pWidth), bottom=ip(pH),
        dynamic=False, color="black",
    )

    wall_t = 7 / 60
    pad_t = wall_t
    cont_L = 600 - 5 - gW
    goal_inner_w = (gW - 10) / 60
    goal_cx = ip(cont_L) + wall_t + goal_inner_w / 2
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

    ball = Ball(
        x=ip(0) + bR / 60, y=ip(sH + sL) + bR / 60,
        radius=bR / 60, color="green", dynamic=True,
    )
    block_x = ip(pL + jitter)
    block_y = ip(pH + pWidth) + bS / 120
    blocking_ball = Ball(x=block_x, y=block_y, radius=bS / 120, color="gray", dynamic=True)

    if flip:
        slope = Wedge(
            x1=flip_x(ip(sW)), y1=ip(sH + sR),
            x2=flip_x(ip(0)), y2=ip(sH + sL),
            bottom=ip(sH),
            dynamic=False, color="black",
        )
        platform = Box(
            left=flip_x(ip(pR)), right=flip_x(ip(pL)),
            top=ip(pH + pWidth), bottom=ip(pH),
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
        ball = Ball(
            x=flip_x(ip(0) + bR / 60), y=ip(sH + sL) + bR / 60,
            radius=bR / 60, color="green", dynamic=True,
        )
        blocking_ball = Ball(x=flip_x(block_x), y=block_y, radius=bS / 120, color="gray", dynamic=True)

    red_ball = Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "slope": slope,
        "platform": platform,
        "container": container,
        "purple_pad": purple_pad,
        "ball": ball,
        "blocking_ball": blocking_ball,
        "red_ball": red_ball,
    }
    return Level(
        name="warden",
        objects=objects,
        action_objects=["red_ball"],
        success_condition=lambda engine: engine.is_in_contact_for_duration(
            "ball", "purple_pad", engine.config.default_success_time
        ),
    )
