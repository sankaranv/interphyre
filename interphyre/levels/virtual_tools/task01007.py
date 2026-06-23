"""task01007 — Remove.

A ball rests on an elevated slope.  A blocking ball sits on a platform above
the container, preventing the task ball from entering.  The player must
remove the blocking ball.
"""

import numpy as np

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Basket, Box, Wedge


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    gW = rng.integers(100, 201)         # container width (VT)
    gH = rng.integers(80, 101)          # container height (VT)
    bR = rng.integers(7, 13)            # task ball radius (VT)
    sL = rng.integers(40, 71)           # slope left extra height above sH (VT)
    sR = rng.integers(5, 11)            # slope right extra height above sH (VT)
    sW = rng.integers(200, 276)         # slope width (VT)
    sH = rng.integers(380, 451)         # slope base height (VT)
    pL = rng.integers(300, 401)         # platform left x (VT)
    pR = rng.integers(475, 501)         # platform right x (VT)
    pH = rng.integers(200, 251)         # platform top y (VT)
    bS = rng.integers(30, 41)          # blocking ball diameter (VT)
    pWidth = 15                         # platform thickness (VT)
    jitter = rng.integers(0, pR - pL)   # blocking ball x offset on platform

    flip = rng.integers(0, 2) == 1

    def ip(v):
        return v / 60 - 5

    def flip_x(x):
        return -x

    # Elevated slope: y ranges from sH to sH+sL (left) and sH+sR (right).
    slope = Wedge(
        x1=ip(0), y1=ip(sH + sL),
        x2=ip(sW), y2=ip(sH + sR),
        bottom=ip(sH),
        dynamic=False, color="black",
    )

    # Platform.
    platform = Box(
        left=ip(pL), right=ip(pR),
        top=ip(pH + pWidth), bottom=ip(pH),
        dynamic=False, color="black",
    )

    wall_t = 7 / 60
    cont_L = 600 - 5 - gW
    goal_inner_w = (gW - 10) / 60
    goal_cx = ip(cont_L) + wall_t + goal_inner_w / 2
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

    # Task ball: at top-left of slope.
    ball = Ball(
        x=ip(0) + bR / 60, y=ip(sH + sL) + bR / 60,
        radius=bR / 60, color="green", dynamic=True,
    )

    # Blocking ball: sits on the platform, above container.
    block_x = ip(pL + jitter)
    block_y = ip(pH + pWidth) + bS / 120  # center = platform top + radius
    blocking_ball = Ball(
        x=block_x, y=block_y,
        radius=bS / 120, color="orange", dynamic=True,
    )

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
        ball = Ball(
            x=flip_x(ip(0) + bR / 60), y=ip(sH + sL) + bR / 60,
            radius=bR / 60, color="green", dynamic=True,
        )
        blocking_ball = Ball(
            x=flip_x(block_x), y=block_y,
            radius=bS / 120, color="orange", dynamic=True,
        )

    red_ball = Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "slope": slope,
        "platform": platform,
        "container": container,
        "ball": ball,
        "blocking_ball": blocking_ball,
        "red_ball": red_ball,
    }
    return Level(
        name="task01007",
        objects=objects,
        action_objects=["red_ball"],
        success_condition=lambda engine: engine.is_in_contact_for_duration(
            "ball", "container", engine.config.default_success_time
        ),
    )
