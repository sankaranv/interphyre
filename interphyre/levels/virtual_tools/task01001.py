"""task01001 — Bridge.

A ball rests on a slope at the right.  It rolls down and across a split
bridge into a container on the left.  The bridge is made of two dynamic bars
with a small gap; the player must bridge the gap to let the ball pass.
"""

import numpy as np

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Bar, Box, Bracket, Wedge


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    # Geometry in VT space (600×600 pixels).
    lW = rng.integers(80, 181)          # container outer width (VT)
    bP = rng.uniform(0.2, 0.8)         # bridge split fraction
    bL = rng.integers(150, 301)         # bridge total length (VT)
    height = rng.integers(60, 201)      # container height and bridge y (VT)
    sR = rng.integers(250, 401)         # slope right-edge height (VT)
    ball_x_vt = rng.integers(500, 576)
    ball_y_vt = rng.integers(425, 526)
    flip = rng.integers(0, 2) == 1

    # Derived
    bridge_start = lW + 22             # VT x where bridge begins
    split_x = bridge_start + bL * bP  # VT x of split
    bridge_end = bridge_start + bL + 2
    sW = max(570, lW + 22 + bL + 2)   # slope left x (VT)

    def ip(v):
        return v / 60 - 5

    def flip_x(x):
        return -x

    wall_t = 7 / 60
    pad_t = wall_t
    goal_inner_w = (lW - 10) / 60
    goal_cx = ip(5) + goal_inner_w / 2 + wall_t
    bracket_y = ip(5)
    pad_y = bracket_y + wall_t * 2

    container = Bracket(
        x=goal_cx,
        y=bracket_y,
        width=goal_inner_w,
        height=height / 60,
        thickness=wall_t,
        dynamic=False,
        color="black",
    )
    purple_pad = Bar(
        left=goal_cx - goal_inner_w / 2,
        right=goal_cx + goal_inner_w / 2,
        y=pad_y,
        thickness=pad_t,
        dynamic=False,
        color="purple",
    )

    # Bridge: two dynamic horizontal Bars.
    bar_t = 10 / 60
    bridge_y = ip(height + 15)
    bridge_L = Bar(
        left=ip(bridge_start), right=ip(split_x),
        y=bridge_y, thickness=bar_t,
        dynamic=True, color="gray",
    )
    bridge_R = Bar(
        left=ip(split_x + 2), right=ip(bridge_end),
        y=bridge_y, thickness=bar_t,
        dynamic=True, color="gray",
    )

    # Left wall lower: from (lW, 0) to (lW+40, height-10) VT.
    lw1 = Box(left=ip(lW), right=ip(lW + 40), top=ip(height - 10), bottom=ip(0), dynamic=False, color="black")
    # Left wall upper notch: from (lW, height-10) to (lW+20, height) VT.
    lw2 = Box(left=ip(lW), right=ip(lW + 20), top=ip(height), bottom=ip(height - 10), dynamic=False, color="black")
    # Right wall lower: from (lW+22+bL+2-50, 0) to (600, height-10) VT.
    rw1 = Box(left=ip(bridge_end - 50), right=ip(600), top=ip(height - 10), bottom=ip(0), dynamic=False, color="black")
    # Right wall upper: from (bridge_end, 0) to (sW, height) VT.
    rw2 = Box(left=ip(bridge_end), right=ip(sW), top=ip(height), bottom=ip(0), dynamic=False, color="black")

    # Slope: trapezoidal piece with bottom at y=height-10, top-left at y=height, top-right at y=sR.
    slope = Wedge(
        x1=ip(sW), y1=ip(height),
        x2=ip(600), y2=ip(sR),
        bottom=ip(height - 10),
        dynamic=False, color="black",
    )

    # Ball
    ball = Ball(x=ip(ball_x_vt), y=ip(ball_y_vt), radius=15 / 60, color="green", dynamic=True)

    if flip:
        # Flip all objects left-right.
        container.x = flip_x(container.x)
        flipped_cx = container.x
        purple_pad = Bar(
            left=flipped_cx - goal_inner_w / 2,
            right=flipped_cx + goal_inner_w / 2,
            y=pad_y,
            thickness=pad_t,
            dynamic=False,
            color="purple",
        )
        bridge_L_left = flip_x(ip(bridge_end))
        bridge_L_right = flip_x(ip(split_x + 2))
        bridge_R_left = flip_x(ip(split_x))
        bridge_R_right = flip_x(ip(bridge_start))
        bridge_L = Bar(left=bridge_L_left, right=bridge_L_right, y=bridge_y, thickness=bar_t, dynamic=True, color="gray")
        bridge_R = Bar(left=bridge_R_left, right=bridge_R_right, y=bridge_y, thickness=bar_t, dynamic=True, color="gray")
        lw1 = Box(left=flip_x(ip(lW + 40)), right=flip_x(ip(lW)), top=ip(height - 10), bottom=ip(0), dynamic=False, color="black")
        lw2 = Box(left=flip_x(ip(lW + 20)), right=flip_x(ip(lW)), top=ip(height), bottom=ip(height - 10), dynamic=False, color="black")
        rw1 = Box(left=ip(-5), right=flip_x(ip(bridge_end - 50)), top=ip(height - 10), bottom=ip(0), dynamic=False, color="black")
        rw2 = Box(left=flip_x(ip(sW)), right=flip_x(ip(bridge_end)), top=ip(height), bottom=ip(0), dynamic=False, color="black")
        slope = Wedge(
            x1=ip(0), y1=ip(sR),
            x2=flip_x(ip(sW)), y2=ip(height),
            bottom=ip(height - 10),
            dynamic=False, color="black",
        )
        ball = Ball(x=flip_x(ip(ball_x_vt)), y=ip(ball_y_vt), radius=15 / 60, color="green", dynamic=True)

    red_ball = Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "container": container,
        "purple_pad": purple_pad,
        "bridge_L": bridge_L,
        "bridge_R": bridge_R,
        "lw1": lw1,
        "lw2": lw2,
        "rw1": rw1,
        "rw2": rw2,
        "slope": slope,
        "ball": ball,
        "red_ball": red_ball,
    }
    return Level(
        name="task01001",
        objects=objects,
        action_objects=["red_ball"],
        success_condition=lambda engine: engine.is_in_contact_for_duration(
            "ball", "purple_pad", engine.config.default_success_time
        ),
    )
