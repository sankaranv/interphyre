"""task01003 — Falling.

A ball is trapped inside a container that is suspended in mid-air.  The
player must cause the container (and ball) to fall so that the ball touches
the floor.
"""

import numpy as np

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Box, Bracket


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    # VT-space geometry.
    cH = rng.integers(50, 101)          # container wall height (VT)
    cB = rng.integers(50, 151)          # container bottom width (VT)
    _ = rng.integers(10, 26)            # left overhang (advances RNG; unused structurally)
    _ = rng.integers(10, 26)            # right overhang (advances RNG; unused structurally)
    cE = rng.integers(10, 301)          # container bottom elevation (VT)
    cX = rng.integers(30, 396)          # container left-bottom x (VT)
    bR = rng.integers(7, 16)            # ball radius (VT)
    flip = rng.integers(0, 2) == 1

    def ip(v):
        return v / 60 - 5

    def flip_x(x):
        return -x

    # Container: dynamic Bracket, center at (cX + cB/2, cE) in VT.
    bracket_t = 7 / 60
    cont_cx = ip(cX + cB / 2)
    # y of bracket body = center of floor bar = cE/60 - 5 (floor bottom at cE VT)
    # The floor bar center sits at cE + bracket_t*60/2 pixels, approximately cE VT.
    cont_y = ip(cE) + bracket_t / 2

    container = Bracket(
        x=cont_cx,
        y=cont_y,
        width=cB / 60,
        height=cH / 60,
        thickness=bracket_t,
        dynamic=True, color="gray",
    )

    # Floor: thin static box at bottom of scene.
    floor_t = 7 / 60
    floor = Box(
        left=-5, right=5,
        top=ip(0) + floor_t, bottom=ip(0),
        dynamic=False, color="black",
    )

    # Task ball: inside the container, just above the floor of the container.
    ball_cx = ip(cX + cB / 2)
    ball_cy = ip(cE) + bR / 60 + bracket_t + 0.05

    ball = Ball(x=ball_cx, y=ball_cy, radius=bR / 60, color="green", dynamic=True)

    if flip:
        container.x = flip_x(cont_cx)
        ball = Ball(x=flip_x(ball_cx), y=ball_cy, radius=bR / 60, color="green", dynamic=True)

    red_ball = Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "container": container,
        "floor": floor,
        "ball": ball,
        "red_ball": red_ball,
    }
    return Level(
        name="free_fall",
        objects=objects,
        action_objects=["red_ball"],
        success_condition=lambda engine: engine.is_in_contact_for_duration(
            "ball", "floor", engine.config.default_success_time
        ),
    )
