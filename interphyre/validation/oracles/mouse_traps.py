"""Targeted oracle for mouse_traps.

Mechanism: Green ball is wedged inside an upside-down basket (jar) on platform1
on the left; blue ball is similarly inside a jar on platform2 on the right.
The jars are tilted open-end inward so the balls need to be knocked out sideways.
An action ball dropped onto or near each basket/ball can tip the basket and
release the ball inside. Once released, both balls fall and meet.

Key parameters:
  green_ball.x is slightly left of platform1.x (inner offset).
  blue_ball.x is slightly right of platform2.x (inner offset).
  Action balls should be placed above each ball to knock or tip the jar.
  The baskets are dynamic, so hitting them causes them to tip and release.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("mouse_traps", max_variants=20, n_attempts=300)


@register_oracle("mouse_traps")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    green = level.objects["green_ball"]
    blue = level.objects["blue_ball"]
    basket1 = level.objects["basket_1"]
    basket2 = level.objects["basket_2"]
    r_red = level.objects["red_ball_1"].radius

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 7:
                # Hit basket1 from the closed side (outer side) to tip it open
                # and release the green ball. basket1 opens to the right (inner),
                # so hit from the left (outer) edge.
                ax1 = float(np.clip(basket1.x + rng.uniform(-0.8, 0.8), -4.5, 4.5))
                ay1 = float(np.clip(green.y + rng.uniform(0.2, 2.0), -4.5, 4.5))

                # Hit basket2 similarly to release the blue ball.
                ax2 = float(np.clip(basket2.x + rng.uniform(-0.8, 0.8), -4.5, 4.5))
                ay2 = float(np.clip(blue.y + rng.uniform(0.2, 2.0), -4.5, 4.5))
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
