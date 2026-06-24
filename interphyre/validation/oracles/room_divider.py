"""Targeted oracle for room_divider.

Mechanism: Green ball starts at the top left, blue ball at the top right.
A pair of stacked horizontal bars (bar_1, bar_2) with a vertical connector
creates a wall blocking horizontal movement. A block_bar prevents the blue ball
from moving right. Floor ramps funnel falling balls toward the center. The
action balls need to knock both target balls off their starting positions so
they fall and meet at the bottom.

Key parameters:
  green_ball near top left; blue_ball near top right.
  Knocking them both downward sends them toward the ramps that converge.
  Place action balls directly above each target ball to initiate falls.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("room_divider", max_variants=20, n_attempts=300)


@register_oracle("room_divider")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    green = level.objects["green_ball"]
    blue = level.objects["blue_ball"]
    bar1 = level.objects["bar_1"]
    r_red = level.objects["red_ball_1"].radius

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 7:
                # Knock green ball leftward so it avoids the vertical wall.
                ax1 = float(np.clip(green.x + rng.uniform(0.2, 1.0), -4.5, 4.5))
                ay1 = float(np.clip(green.y + rng.uniform(-0.3, 1.0), -4.5, 4.5))

                # Knock blue ball downward; it's blocked on the right by block_bar
                # so push it leftward toward the gap.
                ax2 = float(np.clip(blue.x + rng.uniform(0.1, 0.8), -4.5, 4.5))
                ay2 = float(np.clip(blue.y + rng.uniform(-0.3, 1.0), -4.5, 4.5))
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
