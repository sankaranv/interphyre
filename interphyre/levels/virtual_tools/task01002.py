"""task01002 — Catapult.

An L-shaped (arm + fulcrum) catapult rests on a strut.  Dropping the action
ball on the long end launches the task ball into the container on the right.
"""

import numpy as np

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Bar, Basket, Box


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    # VT-space geometry.
    cW = rng.integers(200, 401)          # catapult arm width
    cH = 20                              # arm height (fixed)
    bR = rng.integers(5, 16)            # ball radius (VT)
    sW = rng.integers(10, 51)           # strut width
    sH = rng.integers(60, 201)          # strut height
    gW = rng.integers(60, 151)          # goal (container) width
    gH = rng.integers(60, 181)          # goal height
    cT = rng.integers(5, 11)            # catapult arm thickness
    sp = rng.integers(25, 101)          # gap between container and arm
    stP_raw = rng.integers(0, 151)
    stP = min(stP_raw, int(cW / 2))    # strut position offset along arm
    flip = rng.integers(0, 2) == 1

    # Derived.
    cataCent = 600 - gW - sp - cW // 2   # catapult center x (VT)
    cataLeft = cataCent - cW // 2

    def ip(v):
        return v / 60 - 5

    def flip_x(x):
        return -x

    # Strut: supports the fulcrum of the arm.
    strut = Box(
        left=ip(cataCent - sW // 2 + stP),
        right=ip(cataCent + sW // 2 + stP),
        top=ip(sH),
        bottom=ip(0),
        dynamic=False, color="black",
    )

    # Cradle: left-side stop so the arm can pivot around the strut.
    cradle = Box(
        left=ip(cataLeft),
        right=ip(cataLeft + 10),
        top=ip(sH),
        bottom=ip(0),
        dynamic=False, color="black",
    )

    wall_t = 7 / 60
    goal_inner_w = (gW - 10) / 60
    goal_cx = ip(600 - gW) + goal_inner_w / 2 + wall_t
    container = Basket(
        x=goal_cx,
        y=ip(5),
        bottom_width=goal_inner_w,
        top_width=goal_inner_w,
        height=gH / 60,
        wall_thickness=wall_t,
        floor_thickness=wall_t,
        anchor="bottom_center",
        enable_sensor=False,
        dynamic=False,
        color="purple",
    )

    # Catapult arm: dynamic horizontal bar sitting on top of the strut.
    arm_y = ip(sH + cT // 2)
    arm = Bar(
        left=ip(cataLeft), right=ip(cataLeft + cW),
        y=arm_y, thickness=cT / 60,
        dynamic=True, color="gray",
    )

    # Task ball: sits in the left pocket of the arm.
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
        container = Basket(
            x=flip_x(goal_cx),
            y=ip(5),
            bottom_width=goal_inner_w,
            top_width=goal_inner_w,
            height=gH / 60,
            wall_thickness=wall_t,
            floor_thickness=wall_t,
            anchor="bottom_center",
            enable_sensor=False,
            dynamic=False,
            color="purple",
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
        "arm": arm,
        "ball": ball,
        "red_ball": red_ball,
    }
    return Level(
        name="task01002",
        objects=objects,
        action_objects=["red_ball"],
        success_condition=lambda engine: engine.is_in_contact_for_duration(
            "ball", "container", engine.config.default_success_time
        ),
    )
