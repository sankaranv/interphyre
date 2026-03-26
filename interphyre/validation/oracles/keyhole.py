"""Targeted oracle for keyhole.

Causal chain: green_ball is on the same side as bottom_divider. It must pass through
the gap in top_divider (at x=0) to reach purple_pad on the opposite side. The gap is
near the bottom of top_divider, so the ball needs lateral momentum toward x=0.

B6 fix: place red_ball on the FAR SIDE of green_ball from x=0 (opposite side from
target) so the lateral impulse at contact pushes green_ball TOWARD the center gap.
The old oracle dropped from directly above, creating vertical momentum that sent the
ball into bottom_divider or missing the gap entirely.
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("keyhole")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # push_sign: direction toward x=0 (+1 if ball is on the left, -1 if right).
    # Place red_ball on the OPPOSITE side (away from x=0) to push ball toward gap.
    push_sign = -float(np.sign(green_ball.x))  # direction of push
    push_min = green_ball.radius + radius + 0.05
    push_max = green_ball.radius + radius + 1.5

    for _ in range(n_attempts):
        push_offset = rng.uniform(push_min, push_max)
        # Red_ball on the side AWAY from x=0 to push ball toward center gap.
        x = np.clip(green_ball.x - push_sign * push_offset, -4.5, 4.5)
        y = rng.uniform(green_ball.y - 0.2, green_ball.y + 0.8)
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
