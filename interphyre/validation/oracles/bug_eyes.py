"""Targeted oracle for bug_eyes (across_the_divide).

Solution mechanism (identified from random-search solutions):
  Place each action ball just outside its target ball laterally (slightly past the
  outer edge in x) and below the target ball's starting height.  The action ball
  falls first, bounces off the plateau, then rises.  As the bouncing action ball
  passes through the falling target ball's path, they collide.  The contact normal
  has a horizontal component (inward, toward the centre) that gives the target ball
  enough horizontal velocity to travel over its vertical bar and fall into the shared
  middle zone where the two target balls meet.

Key parameters:
  eps_x ∈ [0.05, 0.6]: x-offset of action ball from target ball centre (outward).
  y_action: starting height of action ball (below target ball, above plateau).
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("bug_eyes", max_variants=50, n_attempts=500)


@register_oracle("bug_eyes")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    green = level.objects["green_ball"]
    blue = level.objects["blue_ball"]
    r_red = level.objects["red_ball_1"].radius

    # Scene limits for clamping.
    x_min, x_max, y_min = -4.5, 4.5, -4.5
    # Target balls start at y≈4.5 (top); action balls must be below them.
    y_max_action = float(green.y) - 0.2

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 8:
                # Primary: place action balls outside each target ball.
                # Outer side of green ball is to the LEFT (smaller x);
                # outer side of blue ball is to the RIGHT (larger x).
                eps_x = rng.uniform(0.05, 0.55)
                y1 = rng.uniform(y_min + 2.0, y_max_action)
                y2 = rng.uniform(y_min + 2.0, y_max_action)

                ax1 = float(np.clip(green.x - eps_x, x_min, x_max))
                ay1 = float(np.clip(y1, y_min, y_max_action))
                ax2 = float(np.clip(blue.x + eps_x, x_min, x_max))
                ay2 = float(np.clip(y2, y_min, y_max_action))
            else:
                # Fallback: fully random to cover edge-case geometries.
                ax1 = float(rng.uniform(x_min, x_max))
                ay1 = float(rng.uniform(y_min, y_max_action))
                ax2 = float(rng.uniform(x_min, x_max))
                ay2 = float(rng.uniform(y_min, y_max_action))

            if _run_attempt(env, [(ax1, ay1, r_red), (ax2, ay2, r_red)]):
                return True
    finally:
        env.close()
    return False
