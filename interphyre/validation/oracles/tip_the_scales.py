"""Targeted oracle for tip_the_scales.

Mechanism: Green ball and blue ball sit on separate small platforms separated
by a vertical separator bar from the top. A tent-shaped floor under one of the
balls funnels it away. The balls need to meet: knocking both balls off their
platforms sends them falling. The separator prevents easy horizontal passage
above a certain height, but below the separator bottom the balls can meet.

Key parameters:
  green_ball at platform_1 center, blue_ball at platform_2 center.
  separator is a vertical bar going down from the top between them.
  Drop action balls above each target ball to knock them off the platforms.
  They will fall past the separator bottom and can then meet at the floor.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("tip_the_scales", max_variants=50, n_attempts=500)


@register_oracle("tip_the_scales")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    green = level.objects["green_ball"]
    blue = level.objects["blue_ball"]
    r_red = level.objects["red_ball_1"].radius

    # Separator bottom: below this y the balls can cross.

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 7:
                # Drop action ball 1 above green ball to knock it off platform_1.
                ax1 = float(np.clip(green.x + rng.uniform(-0.2, 0.2), -4.5, 4.5))
                ay1 = float(np.clip(green.y + rng.uniform(0.3, 2.0), -4.5, 4.5))

                # Drop action ball 2 above blue ball to knock it off platform_2.
                ax2 = float(np.clip(blue.x + rng.uniform(-0.2, 0.2), -4.5, 4.5))
                ay2 = float(np.clip(blue.y + rng.uniform(0.3, 2.0), -4.5, 4.5))
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
