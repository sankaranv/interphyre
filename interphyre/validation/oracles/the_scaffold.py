"""Targeted oracle for the_scaffold.

Mechanism: same rolling-ball-to-container setup as SeeSaw (task01009), but a
dynamic strut props the plank up.  Knocking the strut away allows the plank to
tip and guide the ball into the container.

Two primary strategies tried in rotation:
  1. Drop on the strut to knock it away, letting the plank tip freely.
  2. Drop near the container-side end of the plank to force the tip directly.
  3. Push the task ball toward the container as a direct-delivery fallback.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_defaults, register_oracle

register_defaults("the_scaffold", max_variants=20, n_attempts=400)


@register_oracle("the_scaffold")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    plank = level.objects["plank"]
    strut = level.objects["strut"]
    ball = level.objects["ball"]
    container = level.objects["container"]
    r_red = level.objects["red_ball"].radius

    plank_cx = float(plank.x)
    plank_y = float(plank.y)
    cx = float(container.x)
    container_end = float(plank.right) if cx > plank_cx else float(plank.left)

    strut_cx = float(strut.x)
    strut_top = float(strut.top)
    strut_hw = float(strut.width) / 2

    ball_x = float(ball.x)
    ball_y = float(ball.y)
    ball_r = float(ball.radius)
    toward_container = 1.0 if cx > ball_x else -1.0
    x_min, x_max = -4.5, 4.5

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 4 == 0:
                # Hit the strut to free the plank.
                x_offset = rng.uniform(-strut_hw, strut_hw)
                ax = float(np.clip(strut_cx + x_offset, x_min, x_max))
                ay = float(rng.uniform(strut_top + r_red, 4.5))
            elif i % 4 == 1:
                # Tip the plank at its container end.
                x_offset = rng.uniform(-0.3, 0.3)
                ax = float(np.clip(container_end + x_offset, x_min, x_max))
                ay = float(rng.uniform(plank_y + r_red + 0.05, 4.5))
            elif i % 4 == 2:
                # Push the ball directly toward the container.
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
