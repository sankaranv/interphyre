"""Targeted oracle for zebra_crossing.

Causal chain: green_ball starts at y=4.4 on the left side of a vertical
separator. It must pass through the gap in the separator to reach the
purple_ground on the right. Drop red_ball above the green_ball to push it
downward and slightly toward the separator gap.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("zebra_crossing")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    top_separator = level.objects["top_separator"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    sep_x = top_separator.x

    # Sample near green_ball biased toward the separator to push ball through gap.
    cx = (green_ball.x + sep_x) / 2
    x_min = np.clip(cx - 1.5, -4.5, 4.5)
    x_max = np.clip(cx + 1.5, -4.5, 4.5)
    y_min = np.clip(green_ball.y + 0.1, -4.5, 4.5)
    y_max = np.clip(green_ball.y + 2.0, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
