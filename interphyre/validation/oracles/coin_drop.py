"""Targeted oracle for coin_drop.

Mechanism: The green ball sits above a horizontal bar with a hole in it. The
ball must fall through the hole into the blue basket below. The action balls
are used to nudge or push the green ball horizontally so it aligns with the
hole and falls through. One action ball pushes the green ball toward the hole
from above; the second can help clear any path blockage.

Key parameters:
  The hole is between left_bar.right and right_bar.left at bar_y height.
  Green ball starts above the bar. Place one action ball just above and to the
  side of green ball to nudge it toward the hole. Place the second action ball
  above the hole midpoint to help guide.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("coin_drop", max_variants=20, n_attempts=300)


@register_oracle("coin_drop")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    green = level.objects["green_ball"]
    left_bar = level.objects["left_bar"]
    right_bar = level.objects["right_bar"]
    r_red = level.objects["red_ball_1"].radius

    # Hole midpoint in x; use to guide green ball through the gap.
    hole_mid_x = (left_bar.right + right_bar.left) / 2
    bar_y = left_bar.y

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 7:
                # Place one action ball beside green ball to push it toward the hole.
                # Push from the side opposite the hole.
                if green.x > hole_mid_x:
                    # hole is to the left of green ball — push from right
                    ax1 = float(np.clip(green.x + rng.uniform(0.3, 1.0), -4.5, 4.5))
                else:
                    # hole is to the right of green ball — push from left
                    ax1 = float(np.clip(green.x - rng.uniform(0.3, 1.0), -4.5, 4.5))
                ay1 = float(np.clip(green.y + rng.uniform(-0.5, 0.5), bar_y, 4.5))

                # Second ball above the hole to guide.
                ax2 = float(np.clip(hole_mid_x + rng.uniform(-0.5, 0.5), -4.5, 4.5))
                ay2 = float(np.clip(bar_y + rng.uniform(0.5, 3.0), -4.5, 4.5))
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
