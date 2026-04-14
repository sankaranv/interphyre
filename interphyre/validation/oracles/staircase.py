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

x sampling fix (this version): A sweep study found an 86% oracle false-negative
rate (43/50 sampled impossible seeds were solvable). Root cause: valid placement
windows can be as small as 0.05×0.05 units. Sampling x uniformly over the 9-unit
range [-4.5, 4.5] gives only 3–30% per-pass hit probability for the narrowest
windows, making 50 or even 150 uniform attempts insufficient. Fix: replace uniform
x with an 80/20 mixture — 80% basket-centered Gaussian (σ=1.5) that concentrates
samples in the approach corridor near the basket mouth, plus 20% uniform fallback
to preserve coverage for seeds where the valid placement is far from the basket.
The y sampling and all other logic are unchanged.
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
    basket = level.objects["basket"]
    radius = red_ball.radius

    # Valid placements span the full staircase — from the bottom stair up to
    # just above the green ball start. x must also cover the full staircase
    # width since the ball can be intercepted at any stair.
    stair_ys = [level.objects[k].y for k in level.objects if k.startswith("stair_")]
    y_min = np.clip(min(stair_ys) - 0.5, -4.5, 4.5) if stair_ys else -4.5
    y_max = np.clip(green_ball.y + 0.5, -4.5, 4.5)

    engine = Box2DEngine(level=level, config=config)
    for _ in range(n_attempts):
        if rng.random() < 0.8:
            # Basket-centered x: valid placements cluster near the basket mouth.
            # Gaussian with σ=1.5 concentrates samples in the approach corridor
            # while the clip preserves board bounds.
            x = float(np.clip(rng.normal(basket.x, 1.5), -4.5, 4.5))
        else:
            # Uniform fallback: preserves coverage for seeds where the valid
            # placement is far from the basket center.
            x = rng.uniform(-4.5, 4.5)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("staircase")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None


# Geometric-decay analysis (2026-04-14): p=0.344 per variant, model(k=25)=0.3 impossible.
# k=25 reduces expected impossible from 148 (k=10) to <1 per 10001 seeds.
register_defaults("staircase", max_variants=25, n_attempts=500)
