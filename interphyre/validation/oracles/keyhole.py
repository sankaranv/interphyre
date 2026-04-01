"""Targeted oracle for keyhole.

Causal chain: green_ball is on the same side as bottom_divider. It must pass
through the gap in top_divider (at x=0) to reach purple_pad on the opposite
side. The gap in top_divider is at the BOTTOM of the wall (from MIN_Y up to the
divider's lower edge).

Spec B6 failure mode: the original oracle placed the red ball further than
sum_of_radii from the green ball on the far side. Because both balls start at
rest and fall at the same gravitational rate, the red ball never contacts the
green ball — no lateral impulse is delivered.

Empirically discovered mechanism (floor-bounce):
  1. Place red ball BELOW the green ball (at various heights) and slightly to
     the far side from x=0 (left for left-side seeds, right for right-side).
  2. Both balls fall under gravity. The red ball (starting lower) hits the
     FLOOR first and bounces upward.
  3. The rising red ball contacts the still-falling green ball at a glancing
     angle (small horizontal offset ensures a non-zero horizontal force
     component).
  4. The collision pushes the green ball toward x=0 with lateral velocity.
  5. The green ball navigates past the bottom_divider (which is low enough in
     solvable seeds) and through the keyhole gap, eventually landing on
     purple_pad.

Empirical result (seeds 0–99, max_variants=10, n_attempts=50,
oracle_steps=600): 0% seed exhaustion (100/100 solved).

Note: ~70–75% of individual (seed, variant=0) instances are geometrically
impossible (bottom_divider too tall, gap too tight, or ball positioned such
that the floor-bounce trajectory cannot reach purple_pad). Variants expose
different geometry, resolving most seeds within 10 tries.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, register_solver


@register_solver("keyhole")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Place red ball on the FAR SIDE from x=0 (same side as green_ball, but
    # further from center). For a left-side ball, push_sign=+1 means the red
    # ball is placed at x < green_ball.x (even more left). The floor bounce
    # then imparts a rightward impulse toward the gap.
    push_sign = -float(np.sign(green_ball.x))

    # Maximum safe horizontal offset: don't push red ball past the world boundary.
    max_x_offset = min(0.6, abs(green_ball.x) - 0.2)
    max_x_offset = max(0.05, max_x_offset)  # at least 0.05 offset

    for i in range(n_attempts):
        # Small horizontal offset keeps the collision glancing (diagonal contact
        # normal) so the bounce delivers a horizontal impulse component.
        x_offset = rng.uniform(0.02, max_x_offset)
        x = float(np.clip(green_ball.x - push_sign * x_offset, -4.5, 4.5))

        region = i % 3
        if region == 0:
            # Wide vertical sweep below green_ball: covers the full range of
            # useful drop heights for the floor-bounce trajectory.
            y = float(rng.uniform(-4.0, max(green_ball.y - 0.5, -3.9)))
        elif region == 1:
            # Moderate depth: red ball starts 0.1–2 units below green_ball.
            # Useful when green_ball is near the floor and needs a shallower
            # bounce arc.
            y = float(rng.uniform(max(-4.0, green_ball.y - 2.0), green_ball.y - 0.1))
        else:
            # Near floor: maximises the red ball's upward bounce velocity,
            # useful for seeds where the green ball is high and needs a strong
            # horizontal push.
            y = float(rng.uniform(-4.3, max(-4.3, green_ball.y - 1.0)))

        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("keyhole")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
