"""Targeted oracle for basket_case.

Causal chain: green_ball starts at basket_x (same x as basket) and falls
directly into the basket. Success requires the green_ball to contact
purple_ground. The red_ball must hit the green_ball from the SIDE (at or
slightly below green_ball.y) to deflect it laterally past the basket opening.
Placing above green_ball pushes it further into the basket and reliably fails.
x is focused near basket_x where the collision is reachable; y is at or
just below the green_ball to maximize lateral impulse.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("basket_case")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    basket = level.objects["basket"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # x near basket/green_ball x to ensure a reachable lateral deflection.
    x_min = np.clip(basket.x - 2.5, -4.5, 4.5)
    x_max = np.clip(basket.x + 2.5, -4.5, 4.5)
    # y at or just below green_ball — not above (above pushes into basket).
    y_min = np.clip(green_ball.y - 1.5, -4.5, 4.5)
    y_max = np.clip(green_ball.y + 0.2, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
