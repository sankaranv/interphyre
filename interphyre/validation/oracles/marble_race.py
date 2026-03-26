"""Targeted oracle for marble_race.

Causal chain: green_ball is on the left ramp structure. It needs to roll down
and into the purple_basket at the bottom. The left_beam (gray, dynamic) acts as
a gate — pushing the red_ball into the left_beam drops it, releasing green_ball
to roll along left_ramp_2 → left_ramp_1 → right_ramp → into basket.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("marble_race")
def oracle(level, config, n_attempts, oracle_steps, rng):
    left_beam = level.objects["left_beam"]
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Drop on the left_beam to dislodge it (it is the only dynamic gate).
    # Also accept placements above the green_ball itself.
    x_min = np.clip(left_beam.x - left_beam.length / 2 - 0.5, -4.5, 4.5)
    x_max = np.clip(left_beam.x + left_beam.length / 2 + 0.5, -4.5, 4.5)
    y_min = np.clip(left_beam.y + 0.1, -4.5, 4.5)
    y_max = np.clip(left_beam.y + 3.0, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
