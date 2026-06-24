"""Targeted oracle for dead_weight.

Mechanism: the catapult arm pivots around its support strut.  The task ball sits
near one end of the arm; dropping the red ball on the OPPOSITE end launches the
task ball into the container.

The arm's center x is compared to the ball x to determine which end holds the
task ball — the red ball is aimed at the other end, slightly inboard of the tip
to land on the arm rather than miss it.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_defaults, register_oracle

register_defaults("dead_weight", max_variants=20, n_attempts=300)


@register_oracle("dead_weight")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    arm = level.objects["arm"]
    ball = level.objects["ball"]
    r_red = level.objects["red_ball"].radius

    arm_cx = float(arm.x)
    arm_y = float(arm.y)
    x_min, x_max = -4.5, 4.5

    # Ball is near one tip; drop red ball on the opposite tip.
    if float(ball.x) < arm_cx:
        # Ball on left → drop on right tip
        tip_x = float(arm.right)
        drop_sign = -1.0
    else:
        # Ball on right (flip case) → drop on left tip
        tip_x = float(arm.left)
        drop_sign = 1.0

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 8:
                # Inboard of the tip by a small random offset so red ball lands on arm.
                x_offset = rng.uniform(0.0, abs(arm_cx - tip_x) * 0.5)
                ax = float(np.clip(tip_x + drop_sign * x_offset, x_min, x_max))
                ay = float(rng.uniform(arm_y + r_red, 4.5))
            else:
                ax = float(rng.uniform(x_min, x_max))
                ay = float(rng.uniform(-4.5, 4.5))
            if _run_attempt(env, [(ax, ay, r_red)]):
                return True
    finally:
        env.close()
    return False
