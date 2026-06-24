"""Targeted oracle for double_dutch (double_dutch).

The green ball falls from the top and lands on the upper_bar (the horizontal
obstacle).  It cannot reach the purple_ground on its own.  The lower barriers
have a hole directly below the upper_bar, so once the ball slides off the
upper_bar's edge it falls through to the purple_ground.

Solution: place one action ball slightly to the side of the green ball (same x
zone but shifted left or right).  It also lands on the upper_bar and slides
into the green ball, pushing it off the edge.  The second ball can be placed
anywhere that does not block the ball's exit path.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("double_dutch", max_variants=20, n_attempts=200)


@register_oracle("double_dutch")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    green = level.objects["green_ball"]
    upper_bar = level.objects["upper_bar"]
    r = level.objects["red_ball_1"].radius  # 0.5

    # Upper bar top surface: where the green ball will land.
    bar_top = upper_bar.top
    # The green ball lands on bar_top and needs a lateral push to slide off.
    # The hole in the lower bars is directly below the upper bar, so any
    # direction works.

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 7:
                # Place b1 slightly to the side of the green ball at a height
                # above the upper_bar (so it falls and lands on the bar too,
                # then collides with the green ball).
                eps_x = rng.uniform(0.4, 2.0)
                side = rng.choice([-1, 1])
                ax1 = float(np.clip(green.x + side * eps_x, -4.5, 4.5))
                ay1 = float(rng.uniform(bar_top + 0.5, float(green.y) - 0.2))

                # b2: place away from the path so it doesn't block.
                ax2 = float(rng.uniform(-4.5, -2.5))
                ay2 = float(rng.uniform(-4.5, -1.0))
            else:
                # Full-board random fallback.
                ax1 = float(rng.uniform(-4.5, 4.5))
                ay1 = float(rng.uniform(-4.5, 4.5))
                ax2 = float(rng.uniform(-4.5, 4.5))
                ay2 = float(rng.uniform(-4.5, 4.5))

            if _run_attempt(env, [(ax1, ay1, r), (ax2, ay2, r)]):
                return True
    finally:
        env.close()
    return False
