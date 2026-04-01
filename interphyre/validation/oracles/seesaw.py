"""Targeted oracle for seesaw.

Causal chain: green_ball starts near the top (y~4.5) at a position aligned with
the beam edge. It falls toward the blue_beam. The red_ball should be placed near
the green_ball to guide it precisely onto the beam span.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("seesaw")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    blue_beam = level.objects["blue_beam"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    beam_left = blue_beam.x - blue_beam.length / 2
    beam_right = blue_beam.x + blue_beam.length / 2

    # Stay within beam span in x and drop from above green_ball.
    x_min = np.clip(max(beam_left - 0.5, green_ball.x - 1.5), -4.5, 4.5)
    x_max = np.clip(min(beam_right + 0.5, green_ball.x + 1.5), -4.5, 4.5)
    if x_min >= x_max:
        x_min = np.clip(green_ball.x - 1.5, -4.5, 4.5)
        x_max = np.clip(green_ball.x + 1.5, -4.5, 4.5)

    y_min = np.clip(green_ball.y - 0.5, -4.5, 4.5)
    y_max = np.clip(green_ball.y + 1.0, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
