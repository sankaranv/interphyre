"""Targeted oracle for star_crossed.

Mechanism: Two dynamic Cross standingsticks (left_cross, right_cross) hold
green_ball and blue_ball in their upper V-cups. Tipping either cross releases
its ball onto the inner slopes, which funnel both balls to meet.

Strategy: hit the crosses laterally — left_cross from the right, right_cross
from the left — to tip them. Also try dropping action balls into the cups
directly to dislodge the target balls.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("star_crossed", max_variants=50, n_attempts=500)


@register_oracle("star_crossed")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    left_cross = level.objects["left_cross"]
    right_cross = level.objects["right_cross"]
    green = level.objects["green_ball"]
    blue = level.objects["blue_ball"]
    r_red = level.objects["red_ball_1"].radius

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            mode = i % 12
            if mode < 4:
                # Hit left_cross from the right to tip it left; hit right_cross from the left.
                ax1 = float(np.clip(left_cross.x + rng.uniform(0.3, 2.0), -4.5, 4.5))
                ay1 = float(np.clip(left_cross.y + rng.uniform(-0.5, 0.5), -4.5, 4.5))
                ax2 = float(np.clip(right_cross.x - rng.uniform(0.3, 2.0), -4.5, 4.5))
                ay2 = float(np.clip(right_cross.y + rng.uniform(-0.5, 0.5), -4.5, 4.5))
            elif mode < 7:
                # Drop onto the cups to dislodge both balls.
                ax1 = float(np.clip(green.x + rng.uniform(-0.3, 0.3), -4.5, 4.5))
                ay1 = float(np.clip(green.y + rng.uniform(0.5, 2.5), -4.5, 4.5))
                ax2 = float(np.clip(blue.x + rng.uniform(-0.3, 0.3), -4.5, 4.5))
                ay2 = float(np.clip(blue.y + rng.uniform(0.5, 2.5), -4.5, 4.5))
            elif mode < 10:
                # Wider lateral strikes to maximize torque.
                ax1 = float(np.clip(left_cross.x + rng.uniform(1.0, 3.0), -4.5, 4.5))
                ay1 = float(np.clip(left_cross.y + rng.uniform(-1.0, 1.0), -4.5, 4.5))
                ax2 = float(np.clip(right_cross.x - rng.uniform(1.0, 3.0), -4.5, 4.5))
                ay2 = float(np.clip(right_cross.y + rng.uniform(-1.0, 1.0), -4.5, 4.5))
            else:
                ax1 = float(rng.uniform(-4.5, 4.5))
                ay1 = float(rng.uniform(-4.5, 4.5))
                ax2 = float(rng.uniform(-4.5, 4.5))
                ay2 = float(rng.uniform(-4.5, 4.5))

            if _run_attempt(env, [(ax1, ay1, r_red), (ax2, ay2, r_red)]):
                return True
    finally:
        env.close()
    return False
