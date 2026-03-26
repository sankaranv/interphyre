"""Targeted oracle for the_cradle.

Causal chain: green_ball rests in a V-shaped cradle (two short angled bars meeting at
a junction). Lateral contact from the side dislodges it; vertical drops push it INTO
the V and fail. Place red_ball beside the green_ball at the same height so it lands
on the angled holder bar and rolls into the green_ball.

B1 fix: randomly select LEFT or RIGHT side each attempt so the ball lands on one
of the 5° holder bars and rolls down the slight slope into the green_ball.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("the_cradle")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    for _ in range(n_attempts):
        # Randomly pick left or right side so the ball lands on one holder bar.
        side = rng.choice([-1, 1])
        gap = rng.uniform(0.05, 0.3)
        x = np.clip(
            green_ball.x + side * (green_ball.radius + radius + gap),
            -4.5,
            4.5,
        )
        # At or just above ball center — maximum lateral contact area on the holder bar.
        y = np.clip(rng.uniform(green_ball.y - 0.2, green_ball.y + 0.5), -4.5, 4.5)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
