"""Targeted oracle for the_funnel.

Causal chain: green_ball starts at the top (MAX_Y). The funnel channels it
toward the center gap, then it falls to the floor. The purple_target is on one
side (left or right). A blocker bar deflects the ball away from the non-target
side. Drop red_ball near green_ball on the target side so it enters the funnel
correctly.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, register_solver


@register_solver("the_funnel")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    purple_target = level.objects["purple_target"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Determine target side and bias x toward it from green_ball position.
    target_cx = (purple_target.left + purple_target.right) / 2
    cx = (green_ball.x + target_cx) / 2
    x_min = np.clip(cx - 2.0, -4.5, 4.5)
    x_max = np.clip(cx + 2.0, -4.5, 4.5)
    y_min = np.clip(green_ball.y - 0.3, -4.5, 4.5)
    y_max = np.clip(green_ball.y + 2.0, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("the_funnel")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
