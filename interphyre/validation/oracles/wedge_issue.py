"""Targeted oracle for wedge_issue.

Causal chain: green_ball starts near the top (y~4.0). Two angled bars form a wedge:
black_bar on the left, purple_bar on the right. The ball must land on purple_bar and
maintain contact for the success duration. A slight lateral nudge toward purple_bar
ensures it falls onto the bar rather than past its right end.

B8 fix: place red_ball STRICTLY ABOVE green_ball (y_min = green_ball.y + both radii +
0.05) to eliminate overlap. The old oracle set y_min = green_ball.y - 0.3, which
placed the red_ball BELOW the green_ball center — causing geometric overlap and
explosive contact forces that sent the ball in random directions.
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

    # Strictly above green_ball: no overlap, no explosive contact forces.
    y_min = np.clip(green_ball.y + green_ball.radius + radius + 0.05, -4.5, 4.5)
    y_max = np.clip(green_ball.y + green_ball.radius + radius + 2.0, -4.5, 4.5)

    # x: between green_ball and purple_bar centre to redirect the ball onto the bar.
    cx = (green_ball.x + purple_bar.x) / 2
    x_min = np.clip(cx - 1.0, -4.5, 4.5)
    x_max = np.clip(cx + 1.0, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
