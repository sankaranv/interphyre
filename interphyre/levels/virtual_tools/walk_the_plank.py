"""task01009 — SeeSaw.

A ball rests on a slope; a dynamic plank bridges from the slope edge to near
the container.  The player must tip the plank so the ball rolls into the
container.
"""

import numpy as np

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Bar, Bracket, Wedge


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    sL = rng.integers(200, 401)
    sR = rng.integers(100, 191)
    sW = rng.integers(100, 301)
    goal_w = rng.integers(80, 151)
    flip = rng.integers(0, 2) == 1

    goal_h = int(rng.integers(60, sR))
    goal_L = 600 - goal_w + 5
    goal_R = 600 - 5

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

    wall_t = 7 / 60
    pad_t = wall_t
    goal_inner_w = (goal_R - goal_L - 10) / 60
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
        ball = Ball(x=flip_x(ip(30)), y=ip(sL + 15), radius=15 / 60, color="green", dynamic=True)

    red_ball = Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "slope": slope,
        "plank": plank,
        "container": container,
        "purple_pad": purple_pad,
        "ball": ball,
        "red_ball": red_ball,
    }
    return Level(
        name="walk_the_plank",
        objects=objects,
        action_objects=["red_ball"],
        success_condition=lambda engine: engine.is_in_contact_for_duration(
            "ball", "purple_pad", engine.config.default_success_time
        ),
    )
