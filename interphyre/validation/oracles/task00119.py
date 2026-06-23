"""Targeted oracle for task00119 (the_seesaw_2).

Green ball sits on the far-left end of a dynamic beam (near MIN_X).  Blue
ball sits in a dynamic Basket on the right side of the scene.  They need
to touch.

From solution analysis: one action ball lands NEAR OR IN the basket from
above (x ≈ basket.x ± 2, y > basket.y), knocking the blue ball leftward.
A second ball lands anywhere on the left side (x < 1) to either push the
green ball or deflect the blue ball mid-flight.  Radius r ≈ 0.7–1.3 works.

Strategy: b1 above the basket zone (basket.x - 2 to 4.5, basket.y to 4.5),
b2 random on left half.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("task00119", max_variants=25, n_attempts=1200)


@register_oracle("task00119")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    basket = level.objects["basket"]
    basket_x = float(basket.x)
    basket_y = float(basket.y)

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            r = float(rng.uniform(0.5, 1.3))

            if i % 10 < 7:
                # b1: fall near/into the basket to knock blue ball leftward.
                ax1 = float(rng.uniform(max(-4.5, basket_x - 2.0), 4.5))
                ay1 = float(rng.uniform(basket_y, 4.5))
                # b2: left side of scene (deflect or push green rightward).
                ax2 = float(rng.uniform(-4.5, 1.0))
                ay2 = float(rng.uniform(-4.5, 4.5))
            else:
                ax1 = float(rng.uniform(-4.5, 4.5))
                ay1 = float(rng.uniform(-4.5, 4.5))
                ax2 = float(rng.uniform(-4.5, 4.5))
                ay2 = float(rng.uniform(-4.5, 4.5))

            if _run_attempt(env, [(ax1, ay1, r), (ax2, ay2, r)]):
                return True
    finally:
        env.close()
    return False
