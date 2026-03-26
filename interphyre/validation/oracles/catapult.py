"""Targeted oracle for catapult.

Causal chain: pressing down on the catapult arm RIGHT of the pivot launches the
green_ball (on the left arm tip) toward the blue_ball in the basket on the right
ledge. Drop red_ball between pivot and right arm tip to create the tipping torque.
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

    # Right of pivot = lever arm that lifts the left (green ball) side.
    x_min = np.clip(pivot_ball.x + 0.2, -4.5, 4.5)
    x_max = np.clip(arm_right + 0.3, -4.5, 4.5)
    y_min = np.clip(arm_top + 0.1, -4.5, 4.5)
    y_max = np.clip(arm_top + 3.0, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
