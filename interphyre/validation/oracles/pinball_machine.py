"""Targeted oracle for pinball_machine.

Causal chain: green_ball starts near the top. It must reach the purple_floor
through zigzag star obstacles. Drop red_ball near the green_ball to start it
moving; the stars are small and often leave a path through.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("pinball_machine")
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
