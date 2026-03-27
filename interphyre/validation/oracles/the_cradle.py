"""Targeted oracle for the_cradle.

Causal chain: green_ball rests in a V-shaped cradle formed by two short bars
(left_holder at 175°, right_holder at 5°) meeting at the junction vertex below
the green_ball. The oracle must dislodge green_ball from the V so it falls to
the purple_floor below.

Previous oracle design (now invalid): placed red_ball at (green_ball.x,
holder_y + 0.1), directly overlapping the green_ball. Box2D position-correction
resolved the overlap by launching green_ball upward out of the V. This
placement is rejected by _is_valid_oracle_placement (overlap with green_ball is
forbidden).

Valid-placement approach: near-tangent lateral push from the side of green_ball,
using x_offset ∈ [0.7, 0.99] × sum_r and y placed just above the tangent point.
This creates a near-horizontal contact angle that maximises lateral force on
green_ball. However, the V-cradle geometry resists lateral displacement — the
holder bars constrain green_ball from the sides, and a lateral push merely rolls
it back to the bottom of the V.

Empirical exhaustion with valid placements: ~100% across seeds 0–4 in a dense
30×30 grid scan with 1000 oracle steps. The V-cradle mechanism appears to require
the vertical launch from overlap — no valid placement produces dislodgement.
Documented as an open design issue.
"""
from __future__ import annotations

import math

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("the_cradle")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius
    sum_r = green_ball.radius + radius

    # Near-tangent lateral approach: red_ball placed just above the tangent point
    # beside green_ball. This is the only geometrically valid push that could
    # dislodge a ball from a V-shaped cradle, though empirical testing shows
    # this does not achieve success for any tested seed/variant.
    for i in range(n_attempts):
        side = 1.0 if i % 2 == 0 else -1.0
        x_frac = rng.uniform(0.7, 0.99)
        x_offset = x_frac * sum_r
        y_clearance = math.sqrt(max(0.0, sum_r**2 - x_offset**2))
        x = np.clip(green_ball.x + side * x_offset, -4.5, 4.5)
        y = np.clip(green_ball.y + y_clearance + 0.02, -4.5, 4.5)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
