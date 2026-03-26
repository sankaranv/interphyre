"""Targeted oracle for end_of_line.

Causal chain: green_ball sits on a shelf. It must be knocked off toward the
purple_wall (left or right side wall). Drop red_ball on the far side from the
wall — that is, between the green_ball and the shelf edge on the non-wall side —
to push the ball toward the wall.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("end_of_line")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    purple_wall = level.objects["purple_wall"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    wall_x = purple_wall.x
    ball_x = green_ball.x
    shelf_top = level.objects["shelf"].y + 0.1  # just above shelf

    # Push from the side OPPOSITE the wall — x range between ball and away from wall.
    if wall_x < 0:
        # Wall on left; push from right of ball
        x_min = np.clip(ball_x + 0.2, -4.5, 4.5)
        x_max = np.clip(ball_x + 2.5, -4.5, 4.5)
    else:
        # Wall on right; push from left of ball
        x_min = np.clip(ball_x - 2.5, -4.5, 4.5)
        x_max = np.clip(ball_x - 0.2, -4.5, 4.5)

    y_min = np.clip(shelf_top, -4.5, 4.5)
    y_max = np.clip(shelf_top + 2.5, -4.5, 4.5)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
