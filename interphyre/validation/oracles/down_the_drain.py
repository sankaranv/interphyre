"""Targeted oracle for down_the_drain.

Mechanism: each structure has a target ball (green/blue) caged on a shelf with a
dynamic stick on the outer side and a static vertical wall on the inner side.
Dislodging a target ball requires the red ball to topple its adjacent stick inward,
which knocks the target ball off the shelf into the central channel; ramps at the
floor guide both balls toward the centre where they must touch.

Key parameters:
  stick_1.x: centre-x of the dynamic stick for the green-ball structure (left).
  stick_2.x: centre-x of the dynamic stick for the blue-ball structure (right).
  For the left structure the red ball drops just outside (to the left of) stick_1;
  for the right structure just outside (to the right of) stick_2.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("down_the_drain", max_variants=20, n_attempts=400)


@register_oracle("down_the_drain")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    stick_1 = level.objects["stick_1"]
    stick_2 = level.objects["stick_2"]
    r_red = level.objects["red_ball_1"].radius

    # Target: drop red_ball_1 just left of stick_1, red_ball_2 just right of stick_2.
    # The outer side of stick_1 (left structure) is its left face; outer of stick_2 is right.
    stick1_x = float(stick_1.x)
    stick2_x = float(stick_2.x)
    stick_top_1 = float(stick_1.top)
    stick_top_2 = float(stick_2.top)

    x_min, x_max = -4.5, 4.5

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 7:
                # Primary: land just outside each stick with some height variation.
                x_offset = rng.uniform(r_red, r_red + 0.8)
                ax1 = float(np.clip(stick1_x - x_offset, x_min, x_max))
                ax2 = float(np.clip(stick2_x + x_offset, x_min, x_max))
                # Height anywhere from just above the stick top to the world ceiling.
                ay1 = float(rng.uniform(stick_top_1 + r_red, 4.5))
                ay2 = float(rng.uniform(stick_top_2 + r_red, 4.5))
            else:
                # Fallback: uniform random to catch off-diagonal solutions.
                ax1 = float(rng.uniform(x_min, x_max))
                ay1 = float(rng.uniform(-4.5, 4.5))
                ax2 = float(rng.uniform(x_min, x_max))
                ay2 = float(rng.uniform(-4.5, 4.5))

            if _run_attempt(env, [(ax1, ay1, r_red), (ax2, ay2, r_red)]):
                return True
    finally:
        env.close()
    return False
