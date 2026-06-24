"""Targeted oracle for domino_effect (domino_effect).

The green ball falls from the top and lands on the static obstacle bar.  The
action balls need to push the green ball laterally until it slides off the
obstacle's far edge and falls to the purple_ground.  Both action balls should
land between the green ball and the obstacle to give horizontal impulse from
the SAME side, rolling the ball toward the open edge.

Strategy: place both action balls slightly to the side of the green ball (the
direction toward the obstacle edge is geometry-dependent, so we try both).
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("domino_effect", max_variants=50, n_attempts=500)


@register_oracle("domino_effect")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    green = level.objects["green_ball"]
    obstacle = level.objects["obstacle"]
    r = level.objects["red_ball_1"].radius  # 0.5

    # Determine which edge of the obstacle is closer to the scene boundary
    # (the open side where the green ball can fall off).
    left_gap = obstacle.left - (-5.0)   # gap between obstacle.left and left wall
    right_gap = 5.0 - obstacle.right     # gap between obstacle.right and right wall

    # The "push direction" is toward the farther edge (larger gap means easier exit).
    if left_gap > right_gap:
        push_sign = -1  # push ball left
    else:
        push_sign = 1   # push ball right

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 7:
                # Primary: place both action balls on the push side of the green ball.
                eps1 = rng.uniform(0.3, 2.5)
                eps2 = rng.uniform(0.3, 2.5)
                y1 = rng.uniform(obstacle.top + 0.2, float(green.y) - 0.2)
                y2 = rng.uniform(obstacle.top + 0.2, float(green.y) - 0.2)
                ax1 = float(np.clip(green.x - push_sign * eps1, -4.5, 4.5))
                ay1 = float(np.clip(y1, -4.5, 4.5))
                ax2 = float(np.clip(green.x - push_sign * eps2, -4.5, 4.5))
                ay2 = float(np.clip(y2, -4.5, 4.5))
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
