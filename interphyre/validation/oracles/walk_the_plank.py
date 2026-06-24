"""Targeted oracle for walk_the_plank.

Mechanism: the task ball rolls down a slope toward a dynamic plank that bridges
the gap to the container.  The red ball must tip the plank — specifically its
container-near end — downward so the task ball can cross and fall into the
container.

The container side of the plank is determined by comparing container.x to the
plank center.  The red ball is aimed near the plank end CLOSER to the container
to depress it, creating a ramp toward the container opening.  Secondary
strategy: push the task ball directly toward the container.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_defaults, register_oracle

register_defaults("walk_the_plank", max_variants=20, n_attempts=400)


@register_oracle("walk_the_plank")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    plank = level.objects["plank"]
    ball = level.objects["ball"]
    container = level.objects["container"]
    r_red = level.objects["red_ball"].radius

    plank_cx = float(plank.x)
    plank_y = float(plank.y)
    cx = float(container.x)

    # End of plank nearest the container.
    container_end = float(plank.right) if cx > plank_cx else float(plank.left)
    ball_x = float(ball.x)
    ball_y = float(ball.y)
    ball_r = float(ball.radius)
    toward_container = 1.0 if cx > ball_x else -1.0
    x_min, x_max = -4.5, 4.5

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 3 == 0:
                # Tip the plank near its container end.
                x_offset = rng.uniform(-0.3, 0.3)
                ax = float(np.clip(container_end + x_offset, x_min, x_max))
                ay = float(rng.uniform(plank_y + r_red + 0.05, 4.5))
            elif i % 3 == 1:
                # Push the task ball toward the container.
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
