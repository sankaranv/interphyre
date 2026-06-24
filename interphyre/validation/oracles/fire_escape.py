"""Targeted oracle for fire_escape.

Mechanism: Green ball starts near the top. Staggered bars (with tiny end caps)
zig-zag it down. At the floor, angled traps funnel it to the purple ground at
the center. The success condition is green_ball touching purple_ground. Action
balls can be placed at intermediate bar levels to knock the green ball inward
toward the center corridor, preventing it from bouncing to the sides.

Key parameters:
  green_ball.x: starting x position.
  purple_ground is a horizontal strip in the center at the floor.
  Place action balls in the center column to deflect the ball inward as it falls.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("fire_escape", max_variants=20, n_attempts=300)


@register_oracle("fire_escape")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    green = level.objects["green_ball"]
    purple = level.objects["purple_ground"]
    r_red = level.objects["red_ball_1"].radius

    ground_cx = (purple.left + purple.right) / 2

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 7:
                # Place action balls in the falling path to guide ball toward center.
                ax1 = float(np.clip(ground_cx + rng.uniform(-1.5, 1.5), -4.5, 4.5))
                ay1 = float(np.clip(green.y * rng.uniform(0.3, 0.8), -4.5, 4.5))

                ax2 = float(np.clip(ground_cx + rng.uniform(-1.5, 1.5), -4.5, 4.5))
                ay2 = float(np.clip(green.y * rng.uniform(0.1, 0.5), -4.5, 4.5))
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
