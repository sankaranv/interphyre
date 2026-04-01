"""Targeted oracle for catapult.

Causal chain: red ball dropped on the right arm (right of pivot_ball) adds
torque that rotates the arm, launching green_ball from the left tip rightward
into the basket where blue_ball rests.

Valid-placement geometry: the ball center must sit at least radius above the
arm surface (y ≥ arm_top + radius) to avoid overlapping the catapult_bar. The
effective zone is a narrow band just above the minimum valid height — denser
sampling in y ∈ [arm_top + radius + 0.01, arm_top + radius + 0.3] outperforms
a wider range because low-energy drops give controlled torque without the ball
bouncing off the arm or overshooting.

Empirical exhaustion with valid placements: ~84% of seeds 0–99 are exhausted
at standard bundle parameters (n_attempts=50, oracle_steps=500, max_variants=10).
The remaining ~84% appear genuinely impossible with physically valid placements —
the near-blue exploit (overlapping blue_ball) and the near-zero-height arm
placement (overlapping catapult_bar) that were used previously are both
mechanically invalid and rejected by _is_valid_oracle_placement. This is
documented in spec open question B3; the 10% exhaustion spec target is not
achievable for this level with physically valid placements.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("catapult")
def oracle(level, config, n_attempts, oracle_steps, rng):
    catapult_bar = level.objects["catapult_bar"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    arm_right = catapult_bar.x + catapult_bar.length / 2
    arm_top = catapult_bar.y + catapult_bar.thickness / 2

    # Minimum valid y: ball center must clear the arm surface by at least radius.
    # Empirically the effective zone is a narrow low-height band — samples farther
    # above the surface either miss the arm or add too much energy and overshoot.
    x_min = np.clip(arm_right - 1.5, -4.5, 4.5)
    x_max = np.clip(arm_right, -4.5, 4.5)
    y_min = np.clip(arm_top + radius + 0.01, -4.5, 4.5)
    y_max = np.clip(arm_top + radius + 0.3, -4.5, 4.5)

    if x_min >= x_max or y_min >= y_max:
        return False

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
