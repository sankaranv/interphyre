"""Targeted oracle for straight_face.

Causal chain: green_ball (top, ball_x) must land on purple_pad (target_x, floor).
Gray_ball sits directly below at the same x. The red_ball acts as a deflector:
placed between ball_x and target_x at the gray_ball height, it redirects the
falling stack horizontally toward the pad. Wide x covering both ball and pad
positions, y focused around the gray ball intercept height.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, register_solver


@register_solver("straight_face")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    gray_ball = level.objects["gray_ball"]
    purple_pad = level.objects["purple_pad"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    pad_cx = (purple_pad.left + purple_pad.right) / 2

    # Cover the full lateral span from green_ball.x to pad_cx so the red_ball
    # can act as a deflector anywhere along that path.
    x_lo = min(green_ball.x, pad_cx) - 0.5
    x_hi = max(green_ball.x, pad_cx) + 0.5
    x_min = np.clip(x_lo, -4.5, 4.5)
    x_max = np.clip(x_hi, -4.5, 4.5)

    # y focused around the gray ball intercept height — catching the stack
    # mid-fall gives the most room for lateral redirection.
    y_min = np.clip(gray_ball.y - 1.5, -4.5, 4.5)
    y_max = np.clip(green_ball.y + 0.5, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("straight_face")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
