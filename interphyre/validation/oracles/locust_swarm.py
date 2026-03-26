"""Targeted oracle for locust_swarm.

Causal chain: green_ball starts near the top. It must reach the purple_floor at
the bottom, navigating through two star chains. Drop red_ball near the green_ball
to start it moving downward; the star chains are sparse enough that a direct push
succeeds often enough across seeds.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("locust_swarm")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    x_min = np.clip(green_ball.x - 2.0, -4.5, 4.5)
    x_max = np.clip(green_ball.x + 2.0, -4.5, 4.5)
    y_min = np.clip(green_ball.y + 0.2, -4.5, 4.5)
    y_max = np.clip(green_ball.y + 2.0, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
