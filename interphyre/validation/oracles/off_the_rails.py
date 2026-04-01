"""Targeted oracle for off_the_rails.

Causal chain: green_ball sits in a basket resting on the black_wall. The
purple_wall is to the right (from the black_wall corner). Knocking the basket
or ball toward the purple_wall achieves success. Drop red_ball above the basket.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, register_solver


@register_solver("off_the_rails")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    purple_wall = level.objects["purple_wall"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Target region: between green_ball x and purple_wall center to push toward it.
    wall_cx = purple_wall.x
    cx = (green_ball.x + wall_cx) / 2
    x_min = np.clip(cx - 2.0, -4.5, 4.5)
    x_max = np.clip(cx + 2.0, -4.5, 4.5)
    y_min = np.clip(green_ball.y + 0.2, -4.5, 4.5)
    y_max = np.clip(green_ball.y + 3.5, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("off_the_rails")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
