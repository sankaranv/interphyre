"""Targeted oracle for falling_into_place.

Causal chain: green_ball sits on the bar left or right of the hole. Dropping
red_ball near the green_ball pushes it toward and through the hole in the bar,
then the bottom_ramp bounces it up toward the inverted blue_basket at the top.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("falling_into_place")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Determine hole center from left/right bar edges.
    left_bar = level.objects["left_bar"]
    right_bar = level.objects["right_bar"]
    hole_cx = (left_bar.right + right_bar.left) / 2

    # Push green_ball toward the hole: x between ball and hole center.
    cx = (green_ball.x + hole_cx) / 2
    x_min = np.clip(cx - 1.5, -4.5, 4.5)
    x_max = np.clip(cx + 1.5, -4.5, 4.5)
    y_min = np.clip(green_ball.y + 0.1, -4.5, 4.5)
    y_max = np.clip(green_ball.y + 3.0, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
