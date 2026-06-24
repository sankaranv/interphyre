"""Targeted oracle for hit_the_deck.

Mechanism: same TableA setup (slope + plank + strut) but the container is a
visual decoy.  The true goal is the task ball touching the floor.  The red ball
tips the plank (by hitting the strut or the plank itself) so the ball rolls off
the far edge and falls to the world floor.

Strategy mirrors task01010 but success is checked against the floor contact
condition rather than the container.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_defaults, register_oracle

register_defaults("hit_the_deck", max_variants=20, n_attempts=400)


@register_oracle("hit_the_deck")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    plank = level.objects["plank"]
    strut = level.objects["strut"]
    ball = level.objects["ball"]
    r_red = level.objects["red_ball"].radius

    plank_y = float(plank.y)
    # For floor contact, tip plank away from the slope — drop on the slope-side end.
    slope = level.objects["slope"]
    slope_cx = float(slope.x) if hasattr(slope, "x") else (float(slope.left) + float(slope.right)) / 2
    slope_end = float(plank.left) if slope_cx < float(plank.x) else float(plank.right)

    strut_cx = float(strut.x)
    strut_top = float(strut.top)
    strut_hw = float(strut.width) / 2

    ball_x = float(ball.x)
    ball_y = float(ball.y)
    ball_r = float(ball.radius)
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
                # Tip the plank at the slope-side end (floor-side drops).
                x_offset = rng.uniform(-0.3, 0.3)
                ax = float(np.clip(slope_end + x_offset, x_min, x_max))
                ay = float(rng.uniform(plank_y + r_red + 0.05, 4.5))
            elif i % 4 == 2:
                # Push the task ball directly.
                x_offset = rng.uniform(0.0, ball_r + r_red)
                push_dir = 1.0 if float(plank.right) > ball_x else -1.0
                ax = float(np.clip(ball_x - push_dir * x_offset, x_min, x_max))
                ay = float(rng.uniform(ball_y + ball_r + r_red, 4.5))
            else:
                ax = float(rng.uniform(x_min, x_max))
                ay = float(rng.uniform(-4.5, 4.5))
            if _run_attempt(env, [(ax, ay, r_red)]):
                return True
    finally:
        env.close()
    return False
