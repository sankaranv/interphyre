"""Targeted oracle for low_bridge.

Mechanism: the task ball sits on a table next to a slope ramp.  A ceiling cover
blocks a direct vertical drop into the container.  The red ball must push the
task ball onto the slope so it launches over (or around) the cover and lands in
the container.

The push direction is determined by which side the container is on.  The red
ball is dropped from the OPPOSITE side of the container, above and near the task
ball's x-position, so the collision sends it toward the slope ramp.

Key parameters:
  toward_container: unit direction from ball toward container.
  x_offset: lateral displacement of red ball from ball center (away from container).
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_defaults, register_oracle

register_defaults("low_bridge", max_variants=20, n_attempts=400)


@register_oracle("low_bridge")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    ball = level.objects["ball"]
    container = level.objects["container"]
    r_red = level.objects["red_ball"].radius

    ball_x = float(ball.x)
    ball_y = float(ball.y)
    ball_r = float(ball.radius)
    toward_container = 1.0 if float(container.x) > ball_x else -1.0
    x_min, x_max = -4.5, 4.5

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 8:
                x_offset = rng.uniform(0.0, ball_r * 2 + r_red)
                ax = float(np.clip(ball_x - toward_container * x_offset, x_min, x_max))
                ay = float(rng.uniform(ball_y + ball_r + r_red, 4.5))
            else:
                ax = float(rng.uniform(x_min, x_max))
                ay = float(rng.uniform(-4.5, 4.5))
            if _run_attempt(env, [(ax, ay, r_red)]):
                return True
    finally:
        env.close()
    return False
