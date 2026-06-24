"""Targeted oracle for bottoms_up (the_pitcher).

Two tilted jars (Baskets) hold small balls (radius=0.35) at their sides.  The
action balls must push green toward blue (or vice versa) with a glancing blow.
The target balls are SMALLER than the default action ball radius (0.5), so the
oracle varies r in [0.1, 0.7] to find an effective size.

Strategy: push green RIGHT (place action ball to its LEFT) and push blue LEFT
(place action ball to its RIGHT), with varied height for timing.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("bottoms_up", max_variants=25, n_attempts=400)


@register_oracle("bottoms_up")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    green = level.objects["green_ball"]
    blue = level.objects["blue_ball"]

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            r = float(rng.uniform(0.1, 0.7))

            if i % 10 < 7:
                # Push green RIGHT: place b1 to the left of green.
                eps1 = rng.uniform(0.1, 1.5)
                ax1 = float(np.clip(green.x - eps1, -4.5, 4.5))
                ay1 = float(rng.uniform(-4.5, float(green.y) + 1.0))

                # Push blue LEFT: place b2 to the right of blue.
                eps2 = rng.uniform(0.1, 1.5)
                ax2 = float(np.clip(blue.x + eps2, -4.5, 4.5))
                ay2 = float(rng.uniform(-4.5, float(blue.y) + 1.0))
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
