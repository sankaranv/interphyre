"""Targeted oracle for warden.

Mechanism: a blocking ball sits on a platform above the container opening and
prevents the task ball from entering.  The red ball must knock the blocking ball
off the platform so the task ball can fall into the container.

Strategy: drop the red ball directly above the blocking ball.  A small lateral
offset pushes the blocking ball off either side of the platform.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_defaults, register_oracle

register_defaults("warden", max_variants=20, n_attempts=300)


@register_oracle("warden")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    blocking_ball = level.objects["blocking_ball"]
    r_red = level.objects["red_ball"].radius

    bx = float(blocking_ball.x)
    by = float(blocking_ball.y)
    br = float(blocking_ball.radius)
    x_min, x_max = -4.5, 4.5

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 8:
                x_offset = rng.uniform(-br, br)
                ax = float(np.clip(bx + x_offset, x_min, x_max))
                ay = float(rng.uniform(by + br + r_red, 4.5))
            else:
                ax = float(rng.uniform(x_min, x_max))
                ay = float(rng.uniform(-4.5, 4.5))
            if _run_attempt(env, [(ax, ay, r_red)]):
                return True
    finally:
        env.close()
    return False
