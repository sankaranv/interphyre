"""Targeted oracle for keyhole.

Causal chain: green_ball is on the same side as the bottom_divider (opposite the
purple_pad). It must be pushed through the gap between top_divider bottom and
bottom_divider top. Drop red_ball above the green_ball to send it downward
through the gap and onto the purple_pad.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("keyhole")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Tight band above green_ball — it needs to fall nearly straight down
    # through the narrow gap, so stay close to its x.
    x_min = np.clip(green_ball.x - 1.5, -4.5, 4.5)
    x_max = np.clip(green_ball.x + 1.5, -4.5, 4.5)
    y_min = np.clip(green_ball.y + 0.2, -4.5, 4.5)
    y_max = np.clip(green_ball.y + 2.5, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
