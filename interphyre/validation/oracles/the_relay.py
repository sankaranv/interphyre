"""Targeted oracle for the_relay.

Mechanism: Green ball rests at the left end of ramp1. It must roll right down
ramp1, transfer onto ramp2 going the other direction, fly off the end of ramp2,
clear a vertical wall, and land on the purple ground to the right of the wall.
The action balls can nudge the green ball off ramp1 or help it clear the wall.

Key parameters:
  green_ball sits near ramp1.left at ramp1.top height.
  ramp1 slopes downward left-to-right; ramp2 slopes the other way below it.
  wall is vertical, positioned between ramp2 and purple_ground.
  Place one action ball above/behind green ball to start it rolling.
  Place second action ball to help the ball clear the wall if needed.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("the_relay", max_variants=50, n_attempts=500)


@register_oracle("the_relay")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    green = level.objects["green_ball"]
    wall = level.objects["wall"]
    r_red = level.objects["red_ball_1"].radius

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 7:
                # Place action ball 1 to the left of green ball to push it rightward
                # along ramp1. Slightly above green ball's y.
                ax1 = float(np.clip(green.x - rng.uniform(0.3, 1.5), -4.5, 4.5))
                ay1 = float(np.clip(green.y + rng.uniform(0.0, 1.0), -4.5, 4.5))

                # Place action ball 2 above the wall/ramp2 transition area to help
                # the green ball clear the wall.
                ax2 = float(np.clip(
                    wall.x + rng.uniform(-0.5, 0.5), -4.5, 4.5
                ))
                ay2 = float(np.clip(
                    wall.top + rng.uniform(0.2, 1.5), -4.5, 4.5
                ))
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
