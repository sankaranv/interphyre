"""Targeted oracle for trapeze.

Mechanism: A static Cross (base) stands on the purple_ground. A dynamic Cross
(falling_sticks) leans against the base, tilted at ±35°. Success is
falling_sticks touching purple_ground. The action balls must knock the
falling_sticks off the base so it topples and contacts the ground.

Key parameters:
  falling_sticks.x, falling_sticks.y: center of the dynamic cross.
  The sticks lean left (left=True) or right from the base.
  Place action balls directly above or beside the sticks body to topple it.
  Hit the sticks from the side it leans away from to push it toward the ground.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("trapeze", max_variants=50, n_attempts=500)


@register_oracle("trapeze")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    sticks = level.objects["falling_sticks"]
    base = level.objects["base"]
    r_red = level.objects["red_ball_1"].radius

    # Sticks lean against the base: base is to the right of sticks if left=True.
    # To topple sticks, hit them from the side opposite the base.
    sticks_to_base = base.x - sticks.x  # positive if base is right of sticks

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 7:
                # Hit the sticks body from the side they lean away from.
                # If sticks are left of base, hit from further left to push right.
                if sticks_to_base > 0:
                    ax1 = float(np.clip(sticks.x - rng.uniform(0.5, 2.0), -4.5, 4.5))
                else:
                    ax1 = float(np.clip(sticks.x + rng.uniform(0.5, 2.0), -4.5, 4.5))
                ay1 = float(np.clip(sticks.y + rng.uniform(-0.5, 1.5), -4.5, 4.5))

                # Second ball above the sticks to add downward force.
                ax2 = float(np.clip(sticks.x + rng.uniform(-0.5, 0.5), -4.5, 4.5))
                ay2 = float(np.clip(sticks.y + rng.uniform(0.5, 2.5), -4.5, 4.5))
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
