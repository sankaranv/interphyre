"""Targeted oracle for falling_into_place.

Causal chain: green_ball sits on a horizontal bar left or right of a hole. The ball
must fall through the hole, bounce off bottom_ramp, and reach the inverted blue_basket
at the top. The red_ball must push green_ball toward and through the hole.

B7 fix: place red_ball on the FAR SIDE of green_ball (opposite side from hole) so the
lateral impulse at contact pushes green_ball TOWARD the hole. The old oracle placed
the ball between green_ball and the hole center (wrong side), landing on the bar
surface rather than contacting the green_ball.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("falling_into_place")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    left_bar = level.objects["left_bar"]
    right_bar = level.objects["right_bar"]
    hole_cx = (left_bar.right + right_bar.left) / 2

    # Push from OPPOSITE side: push_direction points from green_ball toward the hole.
    # Placing red_ball on the opposite side creates an impulse pushing toward the hole.
    push_direction = float(np.sign(hole_cx - green_ball.x))
    push_min = green_ball.radius + radius + 0.05
    push_max = green_ball.radius + radius + 1.5

    for _ in range(n_attempts):
        push_offset = rng.uniform(push_min, push_max)
        x = np.clip(green_ball.x - push_direction * push_offset, -4.5, 4.5)
        # Drop from above green_ball with no initial overlap, enough height for force.
        y_base = green_ball.y + green_ball.radius + radius
        y = rng.uniform(np.clip(y_base, -4.5, 4.5), np.clip(y_base + 2.0, -4.5, 4.5))
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
