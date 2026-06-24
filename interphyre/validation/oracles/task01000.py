"""Targeted oracle for task01000 (Basic).

Mechanism: the red ball must hit the green ball and knock it off the table with
enough horizontal velocity to cross the gap and fall into the black bracket.
The push direction is determined by which side the container is on.  The red
ball is dropped from the side OPPOSITE the container, above and near the green
ball, so the collision gives it momentum toward the container.

Key parameters:
  push_away: x-offset of red ball from green ball center (toward away-from-container side).
  drop_height: y starting position of red ball (above ball top).
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("task01000", max_variants=20, n_attempts=400)


@register_oracle("task01000")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    ball = level.objects["ball"]
    container = level.objects["container"]
    r_red = level.objects["red_ball"].radius

    ball_x = float(ball.x)
    ball_y = float(ball.y)
    ball_r = float(ball.radius)

    # Direction from ball toward container; red ball drops from the opposite side.
    toward_container = 1.0 if float(container.x) > ball_x else -1.0
    x_min, x_max = -4.5, 4.5

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 8:
                # Primary: drop slightly to the away-from-container side of the ball.
                x_offset = rng.uniform(0.0, ball_r * 2 + r_red)
                ax = float(np.clip(ball_x - toward_container * x_offset, x_min, x_max))
                ay = float(rng.uniform(ball_y + ball_r + r_red, 4.5))
            else:
                # Fallback: uniform random.
                ax = float(rng.uniform(x_min, x_max))
                ay = float(rng.uniform(-4.5, 4.5))
            if _run_attempt(env, [(ax, ay, r_red)]):
                return True
    finally:
        env.close()
    return False
