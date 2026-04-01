"""Targeted oracle for down_to_earth.

Causal chain: green_ball starts above a platform. It falls and lands on the
platform. Dropping red_ball beside the green_ball pushes it past the platform
edge so it continues to the purple_ground below.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, register_solver


@register_solver("down_to_earth")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    platform = level.objects["platform"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Target near platform edges — just inside or just outside either edge
    # pushes the green ball off the platform.
    x_min = np.clip(platform.left - 1.0, -4.5, 4.5)
    x_max = np.clip(platform.right + 1.0, -4.5, 4.5)
    y_min = np.clip(green_ball.y - 0.5, -4.5, 4.5)
    y_max = np.clip(green_ball.y + 2.0, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("down_to_earth")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
