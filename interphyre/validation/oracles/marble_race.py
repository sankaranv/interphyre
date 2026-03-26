"""Targeted oracle for marble_race.

Causal chain: left_beam (gray, dynamic) is a horizontal gate resting on two black
support balls. Dropping red_ball on the right end of left_beam tips it clockwise
(right end down, left end up) around the left support. This lifts the left end and
opens a gap for green_ball (rolling from left_ramp_2) to pass through → left_ramp_1
→ right_ramp → purple_basket.

B5 fix: concentrate samples on the rightmost 25% of left_beam (outer half of the
right arm, maximising the lever moment) and reduce drop height from 3.0 to 1.5
units for controlled tipping force. The old oracle sampled the full beam width,
so most drops landed near centre (compresses both supports, no tipping).
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("marble_race")
def oracle(level, config, n_attempts, oracle_steps, rng):
    left_beam = level.objects["left_beam"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Right 25% of left_beam for maximum tipping leverage around the left support.
    # left_beam.x is the beam centre; left_beam.x + length*0.25 is 75% from left edge.
    x_min = np.clip(left_beam.x + left_beam.length * 0.25, -4.5, 4.5)
    x_max = np.clip(left_beam.x + left_beam.length / 2 + 0.4, -4.5, 4.5)
    # Low drop height for controlled tipping force (avoids slamming both supports).
    y_min = np.clip(left_beam.y + 0.1, -4.5, 4.5)
    y_max = np.clip(left_beam.y + 1.5, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
