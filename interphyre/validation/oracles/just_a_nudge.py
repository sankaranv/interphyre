"""Targeted oracle for just_a_nudge.

Causal chain: green_ball sits near the LEFT edge of a platform. Dropping red_ball
directly above it knocks it off the left edge → it slides down the left ramp →
falls into the basket where blue_ball rests. Success: green_ball contacts blue_ball.

B2 fix: drop tight band directly above green_ball (x within ±0.8*radius) so the
red_ball always lands on the green_ball rather than on the platform surface between
the ball and the basket center.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("just_a_nudge")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # x: tight band directly above green_ball so the drop always contacts it.
    x_min = np.clip(green_ball.x - green_ball.radius * 0.8, -4.5, 4.5)
    x_max = np.clip(green_ball.x + green_ball.radius * 0.8, -4.5, 4.5)
    # y: above green_ball with enough height for impact force, no initial overlap.
    y_min = np.clip(
        green_ball.y + green_ball.radius + radius, -4.5, 4.5
    )
    y_max = np.clip(
        green_ball.y + green_ball.radius + radius + 2.0, -4.5, 4.5
    )

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
