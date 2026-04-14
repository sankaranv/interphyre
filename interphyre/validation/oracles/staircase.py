"""Targeted oracle for staircase.

Causal chain: green_ball starts at the top (MAX_Y). Stairs step it down to the
right. The purple_basket is at the bottom, guarded by left/right guard bars.
Drop red_ball anywhere along the staircase path to route green_ball into the
basket.

Fix (this version): The original oracle sampled x in [cx +/- 2.0] where
cx = (green_ball.x + basket.x) / 2, and y in [green_ball.y - 0.5,
green_ball.y + 1.0]. Since green_ball.y ~= 4.70, the y window collapsed to
[4.20, 4.50] -- only the top 0.3 units of the board. Full-board sweeps
confirmed valid placements span y in [stair_bottom - 0.5, 4.4], covering the
entire staircase descent. Fix: y from the bottom stair down to the top of the
board.

x sampling analysis (2026-04-14): An initial 20-solution sample suggested
solution x clusters near green_ball.x (mean offset +0.42, range [-0.72, +0.87]).
However, full-bundle analysis of 10001 valid solutions shows x: mean=0.49,
std=2.22 -- nearly uniform across the entire board width. The staircase
intercept position depends on which stair the green_ball is traversing when
the red ball arrives, which varies by seed configuration and is unpredictable
from object positions alone. A two-Gaussian mixture (50% near green_ball,
30% near basket) was tried but gave only 4.3% avg_var improvement (below the
15% threshold) -- worse than expected because the wide solution x distribution
(std=2.22) means Gaussian concentrations near specific x-values miss most
solutions. Reverted to uniform x over the full board; coverage is more
important than density for this level.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
    register_solver,
    Box2DEngine,
)


@register_solver("staircase")
def solver(
    level, config, n_attempts, oracle_steps, rng
) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Valid placements span the full staircase -- from the bottom stair up to
    # just above the green ball start. x covers the full board because the
    # intercept position depends on which stair the ball is at, which varies
    # by seed (solution x std=2.22 across 10001 seeds, essentially uniform).
    stair_ys = [level.objects[k].y for k in level.objects if k.startswith("stair_")]
    y_min = np.clip(min(stair_ys) - 0.5, -4.5, 4.5) if stair_ys else -4.5
    y_max = np.clip(green_ball.y + 0.5, -4.5, 4.5)

    engine = Box2DEngine(level=level, config=config)
    for _ in range(n_attempts):
        # Full-board uniform x: solution x is nearly uniform (std=2.22, mean=0.49)
        # across all seeds. Gaussian concentrations near green_ball.x or basket.x
        # both showed <5% avg_var improvement. Uniform coverage is optimal here.
        x = rng.uniform(-4.5, 4.5)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("staircase")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None


# Staircase oracle: uniform x (full board) + y from stair_bottom to green_ball_top.
# Solution x is nearly uniform (std=2.22 over 10001 seeds) -- Gaussian sampling hurts.
# Trivial rate=11.3%; oracle p_nontrivial~37%; max_variants=25 keeps miss rate low.
register_defaults("staircase", max_variants=25, n_attempts=500)
