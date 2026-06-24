"""Targeted oracle for twin_peaks.

Mechanism: Green ball and blue ball each sit on a small platform above a
vertical tube. Below each tube are ramps that direct them to a shared meeting
area at the floor. The action balls push or knock the target balls off their
platforms so they fall down through the tube and roll along the ramps toward
each other.

Key parameters:
  Each ball sits on top of its horizontal platform (left_bar/right_bar).
  Action balls placed just above and beside each target ball knock them off.
  Once both fall they travel the ramps at the bottom and meet.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("twin_peaks", max_variants=50, n_attempts=500)


@register_oracle("twin_peaks")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    green = level.objects["green_ball"]
    blue = level.objects["blue_ball"]
    r_red = level.objects["red_ball_1"].radius

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 7:
                # Drop action ball 1 directly above green ball to knock it off.
                ax1 = float(np.clip(green.x + rng.uniform(-0.3, 0.3), -4.5, 4.5))
                ay1 = float(np.clip(green.y + rng.uniform(0.3, 2.0), -4.5, 4.5))

                # Drop action ball 2 directly above blue ball to knock it off.
                ax2 = float(np.clip(blue.x + rng.uniform(-0.3, 0.3), -4.5, 4.5))
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
