"""Targeted oracle for mind_the_gap.

Causal chain: green_ball at (0, 3.5) falls toward the platform. A blocking_ball
sits in the hole between left_platform and right_platform. The red_ball must push
the green_ball TOWARD the hole so the green_ball displaces the blocking_ball and
falls through to the purple_ground.

B4 fix: place red_ball on the FAR SIDE of green_ball relative to the hole so the
lateral impulse at contact pushes green_ball toward the hole. The old oracle placed
the ball between green_ball and the hole (wrong side), landing on the platform
surface rather than on the green_ball.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("mind_the_gap")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    left_platform = level.objects["left_platform"]
    right_platform = level.objects["right_platform"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Hole center between the two platform halves.
    hole_cx = (left_platform.right + right_platform.left) / 2

    # Push from the OPPOSITE side: red_ball placed behind green_ball relative to hole.
    # push_direction = +1 if hole is right of ball (push comes from the left).
    push_direction = 1.0 if hole_cx > green_ball.x else -1.0
    push_min = green_ball.radius + radius + 0.1
    push_max = green_ball.radius + radius + 1.5

    for _ in range(n_attempts):
        push_offset = rng.uniform(push_min, push_max)
        x = np.clip(green_ball.x - push_direction * push_offset, -4.5, 4.5)
        y = rng.uniform(green_ball.y - 0.1, green_ball.y + 0.5)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
