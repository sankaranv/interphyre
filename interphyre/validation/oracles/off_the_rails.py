"""Targeted oracle for off_the_rails.

Causal chain: green_ball sits in a basket resting on the black_wall. The
purple_wall is to the right (from the black_wall corner). Knocking the basket
or ball toward the purple_wall achieves success.

Two sampling bands cover the two solution regimes:

Band A (70% of attempts): drop above the basket.
    x in [cx - 2, cx + 2] where cx = midpoint of green_ball and purple_wall.
    y in [green_ball.y + 0.2, green_ball.y + 3.5].
    Works for the majority of seeds where the basket is at a moderate angle and
    there is space above the green_ball to place the action ball.

Band B (30% of attempts): approach from below.
    x in [cx - 2, cx + 2]  (same horizontal range as Band A).
    y in [-4.5, green_ball.y - 0.2].
    Required for seeds where the green_ball is near the top of the board and
    the above-approach collapses to a sliver (< 0.5 units of y range).  In
    these geometries a ball placed below and between the basket/wall delivers
    a lateral impulse through a different causal chain.  Empirically confirmed
    for seed 40 where Band A's y range is [4.05, 4.50] (0.45 units) but valid
    hits cluster at y in [-3.6, +1.1].

Oracle history:
    Original oracle: single band above green_ball, 997/1000 seeds certified.
    Two-band oracle (this version): adds Band B below-green-ball, recovers
    seed 40 -- the primary holdout. Seed 201 certified geometrically impossible
    at all variants. Seed 954 hit pattern at x=-4.5 boundary under investigation.
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

    # Horizontal range: midpoint between green_ball and purple_wall, ±2 units.
    wall_cx = purple_wall.x
    cx = (green_ball.x + wall_cx) / 2
    x_min = float(np.clip(cx - 2.0, -4.5, 4.5))
    x_max = float(np.clip(cx + 2.0, -4.5, 4.5))

    # Band A vertical range: above the green_ball.
    y_min_a = float(np.clip(green_ball.y + 0.2, -4.5, 4.5))
    y_max_a = float(np.clip(green_ball.y + 3.5, -4.5, 4.5))

    # Band B vertical range: below the green_ball (full floor-to-ball range).
    y_max_b = float(np.clip(green_ball.y - 0.2, -4.5, 4.5))

    for i in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        if i % 10 < 7:
            # Band A: drop above.
            if y_min_a >= y_max_a:
                # No space above — fall through to Band B immediately.
                y = rng.uniform(-4.5, y_max_b)
            else:
                y = rng.uniform(y_min_a, y_max_a)
        else:
            # Band B: approach from below.
            y = rng.uniform(-4.5, y_max_b)

        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("off_the_rails")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
