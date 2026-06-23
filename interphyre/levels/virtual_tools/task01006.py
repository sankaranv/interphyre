"""task01006 — Unbox.

Ball on a slope rolls into a container whose opening is blocked by a dynamic
lid.  The player must knock the lid off so the ball can enter.
"""

import numpy as np

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Basket, Box, Wedge


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    sL = rng.integers(200, 401)         # slope left height (VT)
    sR = rng.integers(100, 191)         # slope right height (VT)
    sW = rng.integers(100, 301)         # slope width (VT)
    bpos_x = rng.integers(30, 101)      # ball x (VT)
    bpos_y_offset = rng.integers(15, 51)
    bpos_y = sL + bpos_y_offset         # ball y (VT)
    goal_w = rng.integers(80, 151)      # container inner width (VT)
    lid_extent = rng.integers(10, 51)   # how far lid extends past container right
    lid_t = rng.integers(8, 21)         # lid thickness
    goal_h = rng.integers(60, sR)       # container height

    flip = rng.integers(0, 2) == 1

    def ip(v):
        return v / 60 - 5

    def flip_x(x):
        return -x

    # Slope.
    slope = Wedge(
        x1=ip(0), y1=ip(sL),
        x2=ip(sW), y2=ip(sR),
        bottom=ip(0),
        dynamic=False, color="black",
    )

    goal_L = sW
    goal_R = sW + goal_w
    wall_t = 7 / 60
    goal_inner_w = goal_w / 60 - 2 * wall_t
    goal_cx = ip(goal_L) + wall_t + goal_inner_w / 2
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

    # Lid: sits on top of container opening.
    lid = Box(
        left=ip(goal_L), right=ip(goal_R + lid_extent),
        top=ip(goal_h + 5 + lid_t), bottom=ip(goal_h + 5),
        dynamic=True, color="gray",
    )

    # Ball on slope.
    ball = Ball(x=ip(bpos_x), y=ip(bpos_y), radius=15 / 60, color="green", dynamic=True)

    if flip:
        slope = Wedge(
            x1=flip_x(ip(sW)), y1=ip(sR),
            x2=flip_x(ip(0)), y2=ip(sL),
            bottom=ip(0),
            dynamic=False, color="black",
        )
        container = Basket(
            x=flip_x(goal_cx),
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
        "lid": lid,
        "ball": ball,
        "red_ball": red_ball,
    }
    return Level(
        name="task01006",
        objects=objects,
        action_objects=["red_ball"],
        success_condition=lambda engine: engine.is_in_contact_for_duration(
            "ball", "container", engine.config.default_success_time
        ),
    )
