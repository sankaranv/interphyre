"""Targeted oracle for pass_the_parcel.

Causal chain: inverted top_basket sits on the platform; green_ball is next to it.
Pushing the top_basket off the platform causes green_ball to roll into the bottom
basket and contact the blue_ball. Drop above the top_basket.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, register_solver, Box2DEngine


@register_solver("pass_the_parcel")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    top_basket = level.objects["top_basket"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    x_min = np.clip(top_basket.x - 2.0, -4.5, 4.5)
    x_max = np.clip(top_basket.x + 2.0, -4.5, 4.5)
    y_min = np.clip(top_basket.y + 0.2, -4.5, 4.5)
    y_max = np.clip(top_basket.y + 3.5, -4.5, 4.5)

    engine = Box2DEngine(level=level, config=config)
    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("pass_the_parcel")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
