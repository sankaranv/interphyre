"""Targeted oracle for no_mans_land.

Mechanism: Green ball and blue ball start elevated, separated horizontally.
Success requires green_ball touching blue_ball. Each ball has a basket at the
floor below it. The action balls are placed to push one or both target balls
toward each other, or to knock them off their current positions so they meet.

Key parameters:
  Green ball at green.x, blue ball at blue.x; blue is always to the right.
  Action balls should push each target ball toward the other ball's side.
  Simplest approach: push green ball rightward toward blue ball (or vice versa).
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("no_mans_land", max_variants=20, n_attempts=200)


@register_oracle("no_mans_land")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    green = level.objects["green_ball"]
    blue = level.objects["blue_ball"]
    r_red = level.objects["red_ball_1"].radius

    midpoint_x = (green.x + blue.x) / 2

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 5:
                # Push green ball rightward: place action ball to left of green.
                ax1 = float(np.clip(green.x - rng.uniform(0.3, 1.5), -4.5, 4.5))
                ay1 = float(np.clip(green.y + rng.uniform(-0.3, 0.3), -4.5, 4.5))
                # Push blue ball leftward: place action ball to right of blue.
                ax2 = float(np.clip(blue.x + rng.uniform(0.3, 1.5), -4.5, 4.5))
                ay2 = float(np.clip(blue.y + rng.uniform(-0.3, 0.3), -4.5, 4.5))
            elif i % 10 < 7:
                # Drop both action balls above the midpoint to create a collision.
                ax1 = float(np.clip(midpoint_x + rng.uniform(-0.5, 0.0), -4.5, 4.5))
                ay1 = float(np.clip(green.y + rng.uniform(0.5, 2.0), -4.5, 4.5))
                ax2 = float(np.clip(midpoint_x + rng.uniform(0.0, 0.5), -4.5, 4.5))
                ay2 = float(np.clip(blue.y + rng.uniform(0.5, 2.0), -4.5, 4.5))
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
