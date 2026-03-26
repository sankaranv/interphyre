"""Targeted oracle for flagpole_sitta.

Causal chain: green_ball sits on top of the flagpole. Knocking it off causes it
to fall to the purple_ground. The ceiling is just above the green_ball, so a
lateral drop near the ball is most effective. Sample near the ball position.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("flagpole_sitta")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    flagpole = level.objects["flagpole"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    pole_top = flagpole.y + flagpole.length / 2

    # Tight band around flagpole top — lateral contact knocks ball off cleanly.
    x_min = np.clip(flagpole.x - 2.5, -4.5, 4.5)
    x_max = np.clip(flagpole.x + 2.5, -4.5, 4.5)
    y_min = np.clip(pole_top - 0.5, -4.5, 4.5)
    y_max = np.clip(pole_top + 1.5, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
