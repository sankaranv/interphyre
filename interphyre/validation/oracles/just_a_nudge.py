"""Targeted oracle for just_a_nudge.

Causal chain: the basket is dynamic. Placing red_ball near the basket causes
it to shift horizontally, repositioning it under green_ball's fall trajectory.
Green_ball falls off the platform into the repositioned basket and contacts
blue_ball. Success: green_ball in contact with blue_ball for the required time.

Previous oracle design (now invalid): Phase 1 placed red_ball at (blue_ball.x,
blue_ball.y) — directly overlapping blue_ball — and Phase 2 placed it
overlapping the basket wall. Both exploited Box2D position-correction impulses
to produce a large lateral force on the basket. These placements are rejected
by _is_valid_oracle_placement (overlap with non-action objects is forbidden).

Valid-placement approach: sample from outside the basket walls to create a
lateral push via normal collision. The effective lateral force from a falling
ball on a basket wall is much smaller than the position-correction impulse,
and empirically this does not generate sufficient basket displacement (~0.5–1.5
units required). Validation across seeds 0–19 with valid placements finds no
solutions in dense grid scans.

Empirical exhaustion with valid placements: ~100%. This level's causal
mechanism appears to require a force magnitude that is only achievable via
invalid overlap placements. Documented as an open design issue.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, Box2DEngine


@register_oracle("just_a_nudge")
def oracle(level, config, n_attempts, oracle_steps, rng):
    basket = level.objects["basket"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    hw = basket.total_width / 2
    hh = basket.total_height / 2

    # Sample outside the basket walls (valid placements), alternating sides.
    # Right-side push moves basket left toward green_ball; left-side moves right.
    # Neither generates sufficient displacement with valid drop heights, but this
    # is the only physically valid approach available.
    x_right = np.clip(basket.x + hw + radius + 0.02, -4.5, 4.5)
    x_left = np.clip(basket.x - hw - radius - 0.02, -4.5, 4.5)
    y_min = np.clip(basket.y - hh + radius, -4.5, 4.5)
    y_max = np.clip(basket.y + hh + 1.0, -4.5, 4.5)

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        x = x_right if i % 2 == 0 else x_left
        y = rng.uniform(y_min, y_max)
        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return True
    return False
