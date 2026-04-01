"""Targeted oracle for staircase.

Causal chain: green_ball starts at the top (MAX_Y). Stairs step it down to the
right. The purple_basket is at the bottom, guarded by left/right guard bars.
Drop red_ball above green_ball, biased toward basket_x, to route it into the basket.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("staircase")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    basket = level.objects["basket"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Bias x toward basket center; green_ball is already constrained near basket.x
    cx = (green_ball.x + basket.x) / 2
    x_min = np.clip(cx - 2.0, -4.5, 4.5)
    x_max = np.clip(cx + 2.0, -4.5, 4.5)
    y_min = np.clip(green_ball.y - 0.5, -4.5, 4.5)
    y_max = np.clip(green_ball.y + 1.0, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
