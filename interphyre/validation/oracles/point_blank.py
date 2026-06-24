"""Targeted oracle for point_blank.

Mechanism: Two symmetric elements, each containing a ball wedged by a dynamic
handle bar on a tilted channel with a blocker. Left element has green_ball
pinned by handle_1; right element has blue_ball pinned by handle_2. Knocking
each handle away releases the ball, which then falls onto the catch ramps at
the bottom that funnel both balls to meet in the center.

Key parameters:
  handle_1.x, handle_1.y: dynamic bar pinning green ball in left element.
  handle_2.x, handle_2.y: dynamic bar pinning blue ball in right element.
  obstacle_1 and obstacle_2 block direct action from above, so action balls
  must hit the handles from the side or below the obstacles.
  Place action ball 1 to the side of handle_1 to knock it free.
  Place action ball 2 to the side of handle_2 to knock it free.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("point_blank", max_variants=20, n_attempts=400)


@register_oracle("point_blank")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    handle1 = level.objects["handle_1"]
    handle2 = level.objects["handle_2"]
    obs1 = level.objects["obstacle_1"]
    obs2 = level.objects["obstacle_2"]
    green = level.objects["green_ball"]
    blue = level.objects["blue_ball"]
    r_red = level.objects["red_ball_1"].radius

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 5:
                # Hit handle_1 from the outer left side to knock it away and
                # release green_ball. Must come from below obstacle_1.
                ax1 = float(np.clip(handle1.x - rng.uniform(0.5, 2.0), -4.5, 4.5))
                ay1 = float(np.clip(handle1.y + rng.uniform(-0.5, 0.5), -4.5, obs1.y - 0.1))

                # Hit handle_2 from the outer right side to release blue_ball.
                ax2 = float(np.clip(handle2.x + rng.uniform(0.5, 2.0), -4.5, 4.5))
                ay2 = float(np.clip(handle2.y + rng.uniform(-0.5, 0.5), -4.5, obs2.y - 0.1))
            elif i % 10 < 7:
                # Try dropping action balls above the handles more centrally.
                ax1 = float(np.clip(handle1.x + rng.uniform(-0.5, 0.5), -4.5, 4.5))
                ay1 = float(np.clip(handle1.y + rng.uniform(0.3, 1.5), -4.5, 4.5))
                ax2 = float(np.clip(handle2.x + rng.uniform(-0.5, 0.5), -4.5, 4.5))
                ay2 = float(np.clip(handle2.y + rng.uniform(0.3, 1.5), -4.5, 4.5))
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
