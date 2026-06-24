"""Targeted oracle for slot_machine.

Mechanism: Green ball starts near the top center. It must fall through a maze
of staggered bars (each with small end caps) and reach the purple ground at the
bottom center. The left and right corner traps funnel the ball toward the purple
ground. The action balls can clear a path or nudge the green ball off a bar it
gets stuck on, guiding it toward the purple ground in the middle.

Key parameters:
  green_ball.x: the x position to start from (ball_x).
  purple_ground is centered around ground_center between left_trap.right and
  right_trap.left. Action balls should be placed to knock the green ball free
  if it lands on a bar, directing it downward toward center.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("slot_machine", max_variants=20, n_attempts=300)


@register_oracle("slot_machine")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    green = level.objects["green_ball"]
    purple = level.objects["purple_ground"]
    r_red = level.objects["red_ball_1"].radius

    # Purple ground center for targeting.
    ground_cx = (purple.left + purple.right) / 2

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 7:
                # Place action balls along the vertical column above the purple ground
                # to knock the green ball toward center as it falls.
                ax1 = float(np.clip(ground_cx + rng.uniform(-1.0, 1.0), -4.5, 4.5))
                ay1 = float(np.clip(green.y * rng.uniform(0.3, 0.9), -4.5, 4.5))

                ax2 = float(np.clip(ground_cx + rng.uniform(-1.0, 1.0), -4.5, 4.5))
                ay2 = float(np.clip(green.y * rng.uniform(0.1, 0.6), -4.5, 4.5))
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
