"""Targeted oracle for dive_bomb.

Causal chain: green_ball sits on the angled cannon. Dropping red_ball above the
green_ball pushes it into the cannon chute and out toward the purple_pad.
The cannon exit is to the right of center, so we bias x toward the green_ball.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("dive_bomb")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    x_min = np.clip(green_ball.x - 1.5, -4.5, 4.5)
    x_max = np.clip(green_ball.x + 1.5, -4.5, 4.5)
    y_min = np.clip(green_ball.y + 0.2, -4.5, 4.5)
    y_max = np.clip(green_ball.y + 3.5, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
