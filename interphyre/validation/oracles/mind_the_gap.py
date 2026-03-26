"""Targeted oracle for mind_the_gap.

Causal chain: green_ball is at (0, 3.5) and a blocking_ball sits in the gap
between left and right platform halves. The red_ball must move the blocking_ball
or push the green_ball through the gap. Drop near the hole position.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("mind_the_gap")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    left_platform = level.objects["left_platform"]
    right_platform = level.objects["right_platform"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Hole center between the two platform halves.
    hole_cx = (left_platform.right + right_platform.left) / 2

    # Drop near green_ball biased toward hole center to route it through the gap.
    cx = (green_ball.x + hole_cx) / 2
    x_min = np.clip(cx - 1.5, -4.5, 4.5)
    x_max = np.clip(cx + 1.5, -4.5, 4.5)
    y_min = np.clip(green_ball.y + 0.2, -4.5, 4.5)
    y_max = np.clip(green_ball.y + 2.0, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
