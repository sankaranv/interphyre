"""Targeted oracle for crossing.

Mechanism: the task ball starts in mid-air above the right-side wall (rw2 / slope area)
and needs to reach the container on the opposite side by crossing the bridge.

Primary strategy: drop the red ball BELOW and on the AWAY-FROM-CONTAINER side of the
task ball.  The red ball falls, hits rw2 or the slope structure, bounces upward, and
collides with the falling task ball from below, imparting momentum toward the container.
The task ball then rolls across the bridge and into the container.

Secondary strategy: drop near the gap to push the bridge bars together or to act as a
ramp supplement.

Fallback: uniform random.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_defaults, register_oracle

register_defaults("crossing", max_variants=20, n_attempts=150)


@register_oracle("crossing")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    ball = level.objects["ball"]
    container = level.objects["container"]
    bridge_L = level.objects["bridge_L"]
    bridge_R = level.objects["bridge_R"]
    r_red = level.objects["red_ball"].radius

    ball_x = float(ball.x)
    ball_y = float(ball.y)

    # Container side determines push direction.
    toward_container = 1.0 if float(container.x) > ball_x else -1.0
    gap_x = (float(bridge_L.right) + float(bridge_R.left)) / 2
    bridge_y = float(bridge_L.y)
    x_min, x_max = -4.5, 4.5

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            roll = i % 5
            if roll < 2:
                # Primary: drop below and AWAY-FROM-CONTAINER of task ball.
                # Bounces off surface below, collides with task ball from underneath.
                x_offset = rng.uniform(0.1, 1.5)
                y_offset = rng.uniform(0.2, ball_y - bridge_y + 0.5)
                ax = float(np.clip(ball_x - toward_container * x_offset, x_min, x_max))
                ay = float(np.clip(ball_y - y_offset, -4.5, ball_y - 0.1))
            elif roll == 2:
                # Secondary: drop near the gap — may push bridge bars together.
                ax = float(np.clip(gap_x + rng.uniform(-0.5, 0.5), x_min, x_max))
                ay = float(rng.uniform(bridge_y + r_red, 4.5))
            elif roll == 3:
                # Tertiary: drop directly above/on the task ball (in-flight push).
                ax = float(np.clip(ball_x - toward_container * rng.uniform(0, 1.0), x_min, x_max))
                ay = float(rng.uniform(ball_y, 4.5))
            else:
                ax = float(rng.uniform(x_min, x_max))
                ay = float(rng.uniform(-4.5, 4.5))
            if _run_attempt(env, [(ax, ay, r_red)]):
                return True
    finally:
        env.close()
    return False
