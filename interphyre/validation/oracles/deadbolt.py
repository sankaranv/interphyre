"""Targeted oracle for deadbolt.

Mechanism: Green ball starts at the top center. It must fall through a hole in
the top bar, then through a shifted hole in a lower bar, then contact the
purple floor. The success condition is green_ball touching purple_ground.
The action balls can be used to guide or nudge the green ball if it gets stuck,
but the primary strategy is to place action balls beside the ball at each bar
level to push it toward the correct hole.

Key parameters:
  top bar has a hole between left_top_bar.right and right_top_bar.left.
  bottom bar has a hole between left_bottom_bar.right and right_bottom_bar.left.
  Green ball starts at x=0, top of scene. Place action balls to push it
  sideways toward the top-bar hole, then let gravity carry it through.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("deadbolt", max_variants=20, n_attempts=300)


@register_oracle("deadbolt")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    green = level.objects["green_ball"]
    left_top = level.objects["left_top_bar"]
    right_top = level.objects["right_top_bar"]
    left_bot = level.objects["left_bottom_bar"]
    right_bot = level.objects["right_bottom_bar"]
    r_red = level.objects["red_ball_1"].radius

    # Hole midpoints for the two bars.
    top_hole_mid = (left_top.right + right_top.left) / 2
    bot_hole_mid = (left_bot.right + right_bot.left) / 2
    top_bar_y = left_top.y
    bot_bar_y = left_bot.y

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 7:
                # Push green ball toward the top hole from the opposite side.
                if green.x > top_hole_mid:
                    ax1 = float(np.clip(green.x + rng.uniform(0.2, 0.8), -4.5, 4.5))
                else:
                    ax1 = float(np.clip(green.x - rng.uniform(0.2, 0.8), -4.5, 4.5))
                ay1 = float(np.clip(green.y + rng.uniform(-0.5, 1.0), top_bar_y, 4.5))

                # Second ball near the bottom hole level to guide through.
                ax2 = float(np.clip(bot_hole_mid + rng.uniform(-0.5, 0.5), -4.5, 4.5))
                ay2 = float(np.clip(bot_bar_y + rng.uniform(0.5, 2.0), -4.5, 4.5))
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
