"""task01009 — SeeSaw.

A ball rests on a slope; a dynamic plank bridges from the slope edge to near
the container.  The player must tip the plank so the ball rolls into the
container.
"""

import numpy as np

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Bar, Basket, Wedge


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    sL = rng.integers(200, 401)         # slope left height (VT)
    sR = rng.integers(100, 191)         # slope right height (VT)
    sW = rng.integers(100, 301)         # slope width (VT)
    goal_w = rng.integers(80, 151)      # container inner width (VT)
    flip = rng.integers(0, 2) == 1

    goal_h = int(rng.integers(60, sR))
    goal_L = 600 - goal_w + 5          # container left x (VT)
    goal_R = 600 - 5                   # container right x (VT)

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

    # Dynamic plank bridges slope edge to container.
    plank_left = sW + 15
    plank_right = 600 - goal_w - 8
    plank_y = ip(sR + 5)
    plank = Bar(
        left=ip(plank_left), right=ip(plank_right),
        y=plank_y, thickness=10 / 60,
        dynamic=True, color="gray",
    )

    wall_t = 7 / 60
    goal_inner_w = (goal_R - goal_L - 10) / 60
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

    # Ball: fixed position near top of slope.
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
        ball = Ball(x=flip_x(ip(30)), y=ip(sL + 15), radius=15 / 60, color="green", dynamic=True)

    red_ball = Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "slope": slope,
        "plank": plank,
        "container": container,
        "ball": ball,
        "red_ball": red_ball,
    }
    return Level(
        name="task01009",
        objects=objects,
        action_objects=["red_ball"],
        success_condition=lambda engine: engine.is_in_contact_for_duration(
            "ball", "container", engine.config.default_success_time
        ),
    )
