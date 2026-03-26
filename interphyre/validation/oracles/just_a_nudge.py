"""Targeted oracle for just_a_nudge.

Causal chain: green_ball sits at the left edge of the platform above the basket.
Knocking it off to the left/center sends it down the ramps and into the basket
where the blue_ball is. Drop red_ball near the green_ball to nudge it off.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("just_a_nudge")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    basket = level.objects["basket"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Push green_ball toward the basket center below.
    cx = (green_ball.x + basket.x) / 2
    x_min = np.clip(cx - 1.5, -4.5, 4.5)
    x_max = np.clip(cx + 1.5, -4.5, 4.5)
    y_min = np.clip(green_ball.y + 0.2, -4.5, 4.5)
    y_max = np.clip(green_ball.y + 3.0, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
