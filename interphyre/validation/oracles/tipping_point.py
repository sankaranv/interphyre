"""Targeted oracle for tipping_point.

Causal chain: red_ball must tip the vertical green_bar so it falls and contacts
the purple_wall. The bar is in a basket near the wall. Drop red_ball near the
top of the bar on the wall side so gravity and the impact together tip it over.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("tipping_point")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_bar = level.objects["green_bar"]
    purple_wall = level.objects["purple_wall"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    bar_top = green_bar.y + green_bar.length / 2
    wall_x = purple_wall.x

    # Place red_ball on the wall side of the bar top to apply a tipping moment.
    # x range spans from bar center to halfway toward the wall.
    if wall_x < 0:
        x_min = np.clip(wall_x * 0.3 + green_bar.x * 0.7, -4.5, 4.5)
        x_max = np.clip(green_bar.x + 1.0, -4.5, 4.5)
    else:
        x_min = np.clip(green_bar.x - 1.0, -4.5, 4.5)
        x_max = np.clip(wall_x * 0.3 + green_bar.x * 0.7, -4.5, 4.5)

    y_min = np.clip(bar_top - 1.0, -4.5, 4.5)
    y_max = np.clip(bar_top + 2.0, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
