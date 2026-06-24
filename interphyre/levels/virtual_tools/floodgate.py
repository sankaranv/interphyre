"""task01004 — Gap.

A slope funnels the ball toward a gap between the slope and a container.
A dynamic lid sits over the gap.  The player must move the lid so the ball
can fall into the container.
"""

import numpy as np

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Bar, Box, Bracket, Wedge


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    sL = rng.integers(300, 451)
    sR = rng.integers(200, 351)
    sW = rng.integers(200, 301)
    bX = rng.integers(50, 151)
    gW = rng.integers(60, 201)
    jitterX = rng.integers(5, 26)
    jitterY = rng.integers(-5, 81)
    lidT = rng.integers(15, 41)
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

    bY_surface = sL + (sR - sL) * bX / sW
    ball_offset = rng.integers(15, 51)
    ball = Ball(
        x=ip(bX), y=ip(bY_surface + ball_offset),
        radius=15 / 60, color="green", dynamic=True,
    )

    strut = Box(
        left=ip(sW), right=ip(sW + gW),
        top=ip(sR - 150), bottom=ip(0),
        dynamic=False, color="black",
    )
    lid = Box(
        left=ip(sW + jitterX), right=ip(sW + gW - jitterX),
        top=ip(sR + jitterY + lidT), bottom=ip(sR + jitterY),
        dynamic=True, color="gray",
    )

    wall_t = 7 / 60
    pad_t = wall_t
    goal_inner_w = (550 - (sW + gW) - 10) / 60
    goal_cx = ip(sW + gW) + wall_t + goal_inner_w / 2
    goal_h = (sR - 55) / 60
    bracket_y = ip(5)
    pad_y = bracket_y + wall_t * 2
    inner_w = max(goal_inner_w, 0.2)
    inner_h = max(goal_h, 0.2)

    container = Bracket(
        x=goal_cx, y=bracket_y,
        width=inner_w, height=inner_h,
        thickness=wall_t, dynamic=False, color="black",
    )
    purple_pad = Bar(
        left=goal_cx - inner_w / 2,
        right=goal_cx + inner_w / 2,
        y=pad_y, thickness=pad_t,
        dynamic=False, color="purple",
    )

    if flip:
        slope = Wedge(
            x1=flip_x(ip(sW)), y1=ip(sR),
            x2=flip_x(ip(0)), y2=ip(sL),
            bottom=ip(0),
            dynamic=False, color="black",
        )
        ball = Ball(
            x=flip_x(ip(bX)), y=ip(bY_surface + ball_offset),
            radius=15 / 60, color="green", dynamic=True,
        )
        strut = Box(
            left=flip_x(ip(sW + gW)), right=flip_x(ip(sW)),
            top=ip(sR - 150), bottom=ip(0),
            dynamic=False, color="black",
        )
        lid = Box(
            left=flip_x(ip(sW + gW - jitterX)), right=flip_x(ip(sW + jitterX)),
            top=ip(sR + jitterY + lidT), bottom=ip(sR + jitterY),
            dynamic=True, color="gray",
        )
        fcx = flip_x(goal_cx)
        container = Bracket(
            x=fcx, y=bracket_y,
            width=inner_w, height=inner_h,
            thickness=wall_t, dynamic=False, color="black",
        )
        purple_pad = Bar(
            left=fcx - inner_w / 2,
            right=fcx + inner_w / 2,
            y=pad_y, thickness=pad_t,
            dynamic=False, color="purple",
        )

    red_ball = Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "slope": slope,
        "strut": strut,
        "lid": lid,
        "container": container,
        "purple_pad": purple_pad,
        "ball": ball,
        "red_ball": red_ball,
    }
    return Level(
        name="floodgate",
        objects=objects,
        action_objects=["red_ball"],
        success_condition=lambda engine: engine.is_in_contact_for_duration(
            "ball", "purple_pad", engine.config.default_success_time
        ),
    )
