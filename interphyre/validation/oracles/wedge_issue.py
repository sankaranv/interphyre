"""Targeted oracle for wedge_issue.

Causal chain: green_ball starts near the top (y~4.5). Two angled bars form a
wedge: short black_bar on the left, long purple_bar on the right. The green ball
must land on the purple_bar. Drop red_ball above the green_ball biased toward the
purple_bar side (right) so the ball slides onto it.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("wedge_issue")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    purple_bar = level.objects["purple_bar"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Purple bar spans from center to right wall. Sample above green_ball,
    # biased toward purple_bar center.
    bar_cx = purple_bar.x
    cx = (green_ball.x + bar_cx) / 2
    x_min = np.clip(cx - 1.5, -4.5, 4.5)
    x_max = np.clip(cx + 1.5, -4.5, 4.5)
    y_min = np.clip(green_ball.y - 0.3, -4.5, 4.5)
    y_max = np.clip(green_ball.y + 2.0, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
