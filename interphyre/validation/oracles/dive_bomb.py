"""Targeted oracle for dive_bomb.

Causal chain: green_ball sits on the angled cannon. Dropping red_ball above the
green_ball pushes it into the cannon chute and out toward the purple_pad.
The cannon exit is to the right of center, so we bias x toward the green_ball.

Two-zone oracle (this version): The original oracle sampled only above
green_ball (y ∈ [gb.y + 0.2, gb.y + 3.5]). Full-board sweeps of the 14 true
oracle-failure seeds confirmed valid placements cluster near the cannon ramp
exit (x ≈ ramp.x ± 2, y ≈ ramp.y - 2.5 to ramp.y + 1.5), which is
consistently below and to the right of green_ball. Added Zone B (30% of
attempts) covering the ramp-exit region.

Note: ~24% of seeds in this level are "trivial" (green_ball already rests on
purple_pad before any action). These are correctly handled separately by the
bundle generator and should be counted as solvable, not impossible.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, register_solver, Box2DEngine


@register_solver("dive_bomb")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    ramp = level.objects["ramp"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Zone A: above green_ball — standard chute-push mechanism.
    x_min_a = float(np.clip(green_ball.x - 1.5, -4.5, 4.5))
    x_max_a = float(np.clip(green_ball.x + 1.5, -4.5, 4.5))
    y_min_a = float(np.clip(green_ball.y + 0.2, -4.5, 4.5))
    y_max_a = float(np.clip(green_ball.y + 3.5, -4.5, 4.5))

    # Zone B: near cannon ramp exit — covers seeds where valid drops are below
    # and right of green_ball, near where the ball exits the cannon onto the
    # ramp. Confirmed by full-board sweeps of all 14 true-oracle-failure seeds.
    x_min_b = float(np.clip(ramp.x - 2.0, -4.5, 4.5))
    x_max_b = float(np.clip(ramp.x + 2.0, -4.5, 4.5))
    y_min_b = float(np.clip(ramp.y - 2.5, -4.5, 4.5))
    y_max_b = float(np.clip(ramp.y + 1.5, -4.5, 4.5))

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        if i % 10 < 7:
            # Zone A (70%): above green_ball.
            x = rng.uniform(x_min_a, x_max_a)
            y = rng.uniform(y_min_a, y_max_a)
        else:
            # Zone B (30%): ramp-exit region below/right of green_ball.
            x = rng.uniform(x_min_b, x_max_b)
            y = rng.uniform(y_min_b, y_max_b)
        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("dive_bomb")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
