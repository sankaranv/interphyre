"""Targeted oracle for the_cradle.

Causal chain: green_ball rests in a V-shaped cradle (two short angled bars).
Hitting it from above or sideways dislodges it so it falls to the purple_floor.
Drop red_ball near or above the green_ball.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("the_cradle")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    x_min = np.clip(green_ball.x - 2.0, -4.5, 4.5)
    x_max = np.clip(green_ball.x + 2.0, -4.5, 4.5)
    y_min = np.clip(green_ball.y + 0.1, -4.5, 4.5)
    y_max = np.clip(green_ball.y + 3.0, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
