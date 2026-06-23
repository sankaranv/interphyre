"""task01004 — Gap.

A slope funnels the ball toward a gap between the slope and a container.
A dynamic lid sits over the gap.  The player must move the lid so the ball
can fall into the container.
"""

import numpy as np

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Basket, Box, Wedge


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    sL = rng.integers(300, 451)         # slope left height (VT)
    sR = rng.integers(200, 351)         # slope right height (VT)
    sW = rng.integers(200, 301)         # slope width (VT)
    bX = rng.integers(50, 151)          # ball x on slope (VT)
    gW = rng.integers(60, 201)          # gap / strut width (VT)
    jitterX = rng.integers(5, 26)       # lid horizontal inset
    jitterY = rng.integers(-5, 81)      # lid vertical offset from slope edge
    lidT = rng.integers(15, 41)         # lid thickness
    flip = rng.integers(0, 2) == 1

    def ip(v):
        return v / 60 - 5

    def flip_x(x):
        return -x

    # Slope: left edge rises from floor to sL, right edge to sR.
    slope = Wedge(
        x1=ip(0), y1=ip(sL),
        x2=ip(sW), y2=ip(sR),
        bottom=ip(0),
        dynamic=False, color="black",
    )

    # Ball: rests on the slope surface.
    # Linear interpolation: height at bX = sL + (sR - sL) * bX / sW
    bY_surface = sL + (sR - sL) * bX / sW
    ball_offset = rng.integers(15, 51)    # pixels above slope at that x
    ball = Ball(
        x=ip(bX), y=ip(bY_surface + ball_offset),
        radius=15 / 60, color="green", dynamic=True,
    )

    # Strut box: fills from slope right edge to container left edge.
    strut = Box(
        left=ip(sW), right=ip(sW + gW),
        top=ip(sR - 150), bottom=ip(0),
        dynamic=False, color="black",
    )

    # Lid: dynamic box across the top of the strut.
    lid = Box(
        left=ip(sW + jitterX), right=ip(sW + gW - jitterX),
        top=ip(sR + jitterY + lidT), bottom=ip(sR + jitterY),
        dynamic=True, color="gray",
    )

    wall_t = 7 / 60
    goal_inner_w = (550 - (sW + gW) - 10) / 60
    goal_cx = ip(sW + gW) + wall_t + goal_inner_w / 2
    goal_h = (sR - 55) / 60

    container = Basket(
        x=goal_cx,
        y=ip(5),
        bottom_width=max(goal_inner_w, 0.2),
        top_width=max(goal_inner_w, 0.2),
        height=max(goal_h, 0.2),
        wall_thickness=wall_t,
        floor_thickness=wall_t,
        anchor="bottom_center",
        enable_sensor=False,
        dynamic=False,
        color="purple",
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
        container = Basket(
            x=flip_x(goal_cx),
            y=ip(5),
            bottom_width=max(goal_inner_w, 0.2),
            top_width=max(goal_inner_w, 0.2),
            height=max(goal_h, 0.2),
            wall_thickness=wall_t,
            floor_thickness=wall_t,
            anchor="bottom_center",
            enable_sensor=False,
            dynamic=False,
            color="purple",
        )

    red_ball = Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "slope": slope,
        "strut": strut,
        "lid": lid,
        "container": container,
        "ball": ball,
        "red_ball": red_ball,
    }
    return Level(
        name="task01004",
        objects=objects,
        action_objects=["red_ball"],
        success_condition=lambda engine: engine.is_in_contact_for_duration(
            "ball", "container", engine.config.default_success_time
        ),
    )
