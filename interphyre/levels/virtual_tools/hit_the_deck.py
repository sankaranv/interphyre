"""task01011 — TableB.

Same as TableA (task01010) but the goal is for the ball to reach the floor,
not the container.  The container is still visible but is not the success
condition.
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
    goal_w = rng.integers(80, 151)
    strut_w = rng.integers(15, 41)
    flip = rng.integers(0, 2) == 1

    goal_h = int(rng.integers(60, sR))
    goal_L = 600 - goal_w + 5
    goal_R = 600 - 5

    strut_h = rng.integers(40, sR - 9)
    strut_L_min = sW
    strut_L_max = max(sW + 1, int((sW + goal_L) / 2 - strut_w))
    strut_L = rng.integers(strut_L_min, max(strut_L_min + 1, strut_L_max))

    floor_h_vt = 7   # VT pixels — floor thickness

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

    plank_left = sW + 15
    plank_right = 600 - goal_w - 8
    plank_y = ip(sR + 5)
    plank = Bar(
        left=ip(plank_left), right=ip(plank_right),
        y=plank_y, thickness=10 / 60,
        dynamic=True, color="gray",
    )

    # Dynamic strut: base at floor top (floor_h_vt) instead of 0.
    strut = Box(
        left=ip(strut_L), right=ip(strut_L + strut_w),
        top=ip(strut_h), bottom=ip(floor_h_vt),
        dynamic=True, color="gray",
    )

    # Partial floor from slope right edge to right wall.
    floor = Box(
        left=ip(sW), right=ip(600 - 5),
        top=ip(floor_h_vt), bottom=ip(0),
        dynamic=False, color="black",
    )

    # Container: visual only (not the success target).
    bracket_t = 7 / 60
    bracket_floor_y = ip(floor_h_vt) + bracket_t / 2
    goal_inner_w = (goal_R - goal_L - 10) / 60
    goal_cx = ip(goal_L) + bracket_t + goal_inner_w / 2
    container = Bracket(
        x=goal_cx,
        y=bracket_floor_y,
        width=goal_inner_w,
        height=goal_h / 60,
        thickness=bracket_t,
        dynamic=False, color="black",
    )

    ball = Ball(x=ip(30), y=ip(sL + 15), radius=15 / 60, color="green", dynamic=True)

    if flip:
        slope = Wedge(
            x1=flip_x(ip(sW)), y1=ip(sR),
            x2=flip_x(ip(0)), y2=ip(sL),
            bottom=ip(0),
            dynamic=False, color="black",
        )
        plank = Bar(
            left=flip_x(ip(plank_right)), right=flip_x(ip(plank_left)),
            y=plank_y, thickness=10 / 60,
            dynamic=True, color="gray",
        )
        strut = Box(
            left=flip_x(ip(strut_L + strut_w)), right=flip_x(ip(strut_L)),
            top=ip(strut_h), bottom=ip(floor_h_vt),
            dynamic=True, color="gray",
        )
        floor = Box(
            left=ip(5), right=flip_x(ip(sW)),
            top=ip(floor_h_vt), bottom=ip(0),
            dynamic=False, color="black",
        )
        container = Bracket(
            x=flip_x(goal_cx),
            y=bracket_floor_y,
            width=goal_inner_w,
            height=goal_h / 60,
            thickness=bracket_t,
            dynamic=False, color="black",
        )
        ball = Ball(x=flip_x(ip(30)), y=ip(sL + 15), radius=15 / 60, color="green", dynamic=True)

    red_ball = Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "slope": slope,
        "plank": plank,
        "strut": strut,
        "floor": floor,
        "container": container,
        "ball": ball,
        "red_ball": red_ball,
    }
    return Level(
        name="hit_the_deck",
        objects=objects,
        action_objects=["red_ball"],
        success_condition=lambda engine: engine.is_in_contact_for_duration(
            "ball", "floor", engine.config.default_success_time
        ),
    )
