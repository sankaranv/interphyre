"""Targeted oracle for task00116 (the_catapult_2).

Green ball sits on the LEFT end of a horizontal catapult arm (line) that
balances on a hinge_ball.  The purple_ground is to the LEFT of a vertical
left_bar.  Two large action balls (r≈0.8–1.4) must land on the RIGHT half of
the catapult arm, tipping the left end up so the green ball clears the
left_bar and falls onto the purple_ground.

Strategy: place both action balls above the arm's right half — from line.x to
line.right + r, at height line.top to 4.5.  The arm's right end is where the
blue_ball (counterweight) rests, so large balls there transfer maximum torque.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("task00116", max_variants=30, n_attempts=500)


@register_oracle("task00116")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    line = level.objects["line"]
    arm_right = float(line.x + line.length / 2)
    arm_top = float(line.top)

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            r = float(rng.uniform(0.5, 1.5))

            if i % 10 < 8:
                # Drop onto the right half of the catapult arm.
                ax1 = float(rng.uniform(float(line.x), min(arm_right + r, 4.5)))
                ay1 = float(rng.uniform(arm_top, 4.5))
                ax2 = float(rng.uniform(float(line.x), min(arm_right + r, 4.5)))
                ay2 = float(rng.uniform(arm_top, 4.5))
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
