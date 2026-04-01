"""Targeted oracle for zebra_crossing.

Causal chain: green_ball starts near the top (y ≈ 4.4) on the left side of a
vertical separator. Red ball placed below the green_ball (in the diagonal-bar
region) creates a chain reaction through the stacked bars and separator gap,
causing green_ball to fall to the right side and reach purple_ground.

Valid-placement geometry: green_ball.y ≈ 4.4 and red_ball.radius = 0.5, so
the minimum non-overlapping y above green_ball is 4.4 + 0.4 + 0.5 = 5.3,
which exceeds the world boundary (MAX_Y - radius = 4.5). Placing above the
green_ball is geometrically impossible. The effective zone is BELOW the
green_ball, in the y ∈ [green_ball.y - 2.0, green_ball.y - sum_r - 0.01]
band, where red_ball interacts with the diagonal bars and separator.

Empirical exhaustion: ~90% of seeds are solved at standard parameters
(n_attempts=50, oracle_steps=500).
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, register_solver


@register_solver("zebra_crossing")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius
    sum_r = green_ball.radius + radius

    # Effective zone: below green_ball where diagonal bars redirect the ball.
    # The minimum non-overlapping y above green_ball exceeds the world boundary,
    # so all samples must be placed below (y < green_ball.y - sum_r).
    x_min = np.clip(green_ball.x - 1.5, -4.5, 4.5)
    x_max = np.clip(green_ball.x + 1.5, -4.5, 4.5)
    y_min = np.clip(green_ball.y - 2.0, -4.5, 4.5)
    y_max = np.clip(green_ball.y - sum_r - 0.01, -4.5, 4.5)

    if x_min >= x_max or y_min >= y_max:
        return None

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("zebra_crossing")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
