"""Targeted oracle for crucifix.

Mechanism: A small green_ball is cradled inside a dynamic Cross (sticks) which
sits on a small base platform. A static top_bar traps the sticks from above. Two
small gray flanking balls sit at the sides of the base. Success is green_ball
touching purple_ground at the floor. The action balls must topple the sticks
(by pushing the flanking balls or hitting the sticks directly) so the green ball
escapes and falls to the purple ground.

Key parameters:
  sticks.x, sticks.y: center of the dynamic cross holding the ball.
  base.x: horizontal center of the platform.
  flanking balls (left_ball, right_ball) are just beside the base.
  Hit the sticks from the side or knock a flanking ball into the base to tip it.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("crucifix", max_variants=50, n_attempts=500)


@register_oracle("crucifix")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    sticks = level.objects["sticks"]
    left_ball = level.objects["left_ball"]
    right_ball = level.objects["right_ball"]
    r_red = level.objects["red_ball_1"].radius

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            mode = i % 12
            if mode < 3:
                # Drop onto sticks from above — ball falls into the V, toppling sticks sideways.
                ax1 = float(np.clip(sticks.x + rng.uniform(-0.3, 0.3), -4.5, 4.5))
                ay1 = float(np.clip(sticks.y + rng.uniform(1.0, 3.0), -4.5, 4.5))
                ax2 = float(np.clip(sticks.x + rng.uniform(-0.3, 0.3), -4.5, 4.5))
                ay2 = float(np.clip(sticks.y + rng.uniform(1.0, 3.0), -4.5, 4.5))
            elif mode < 6:
                # Strike sticks laterally: one from the left, one from the right.
                ax1 = float(np.clip(sticks.x - rng.uniform(0.4, 2.0), -4.5, 4.5))
                ay1 = float(np.clip(sticks.y + rng.uniform(-0.3, 0.3), -4.5, 4.5))
                ax2 = float(np.clip(sticks.x + rng.uniform(0.4, 2.0), -4.5, 4.5))
                ay2 = float(np.clip(sticks.y + rng.uniform(-0.3, 0.3), -4.5, 4.5))
            elif mode < 9:
                # Push flanking balls inward to destabilize the base.
                ax1 = float(np.clip(left_ball.x - rng.uniform(0.3, 1.5), -4.5, 4.5))
                ay1 = float(np.clip(left_ball.y + rng.uniform(-0.2, 0.3), -4.5, 4.5))
                ax2 = float(np.clip(right_ball.x + rng.uniform(0.3, 1.5), -4.5, 4.5))
                ay2 = float(np.clip(right_ball.y + rng.uniform(-0.2, 0.3), -4.5, 4.5))
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
