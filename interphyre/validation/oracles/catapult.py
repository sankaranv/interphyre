"""Targeted oracle for catapult.

Causal chain: pressing the right arm of the catapult bar (right of pivot_ball)
rotates the arm, launching green_ball from the left tip into the basket.
Concentrating on the outer half of the right arm maximises the lever moment;
a low drop height (1.0 vs 3.0) reduces overshoot and launches the ball on a
tighter arc into the basket.

B3 fix: sample x from the outer half of the right arm only, reduce y range
from 3 to 1 unit above the arm surface.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("catapult")
def oracle(level, config, n_attempts, oracle_steps, rng):
    pivot_ball = level.objects["pivot_ball"]
    catapult_bar = level.objects["catapult_bar"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    arm_right = catapult_bar.x + catapult_bar.length / 2
    arm_top = catapult_bar.y + catapult_bar.thickness / 2

    # Outer half of the right arm: maximum lever distance from the pivot.
    x_min = np.clip(pivot_ball.x + (arm_right - pivot_ball.x) * 0.5, -4.5, 4.5)
    x_max = np.clip(arm_right + 0.2, -4.5, 4.5)
    # Low drop height: controlled tipping force, prevents overshooting the basket.
    y_min = np.clip(arm_top + 0.05, -4.5, 4.5)
    y_max = np.clip(arm_top + 1.0, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
