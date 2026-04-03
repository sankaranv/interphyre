"""Targeted oracle for staircase.

Causal chain: green_ball starts at the top (MAX_Y). Stairs step it down to the
right. The purple_basket is at the bottom, guarded by left/right guard bars.
Drop red_ball anywhere along the staircase path to route green_ball into the
basket.

Fix (this version): The original oracle sampled x ∈ [cx ± 2.0] where
cx = (green_ball.x + basket.x) / 2, and y ∈ [green_ball.y − 0.5,
green_ball.y + 1.0]. Since green_ball.y ≈ 4.70, the y window collapsed to
[4.20, 4.50] — only the top 0.3 units of the board. Full-board sweeps
confirmed valid placements span y ∈ [stair_bottom − 0.5, 4.4], covering the
entire staircase descent. The x centering toward basket was also misleading
when green_ball and basket are far apart. Fix: full-board x and y from the
bottom stair down to the top of the board.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, register_solver, Box2DEngine


@register_solver("staircase")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Valid placements span the full staircase — from the bottom stair up to
    # just above the green ball start. x must also cover the full staircase
    # width since the ball can be intercepted at any stair.
    stair_ys = [level.objects[k].y for k in level.objects if k.startswith("stair_")]
    y_min = np.clip(min(stair_ys) - 0.5, -4.5, 4.5) if stair_ys else -4.5
    y_max = np.clip(green_ball.y + 0.5, -4.5, 4.5)

    engine = Box2DEngine(level=level, config=config)
    for _ in range(n_attempts):
        x = rng.uniform(-4.5, 4.5)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("staircase")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
