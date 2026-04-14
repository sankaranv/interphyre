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

x sampling fix (this version): Analysis of 20 sampled valid solutions showed that
solution x clusters tightly near green_ball.x (mean offset = +0.42 units, range
[-0.72, +0.87]) rather than near basket.x (which can be 1–2 units away). The
previous 80/20 basket-centered Gaussian (σ=1.5) systematically missed when the
two were far apart, yielding p=0.34 per variant. Fix: replace with a two-Gaussian
mixture — 50% Gaussian(green_ball.x, σ=0.8) targeting the solution cluster, 30%
Gaussian(basket.x, σ=1.2) preserving the approach-corridor coverage, and 20%
uniform fallback for out-of-cluster seeds. Expected per-variant p ~0.55.
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
        draw = rng.random()
        if draw < 0.5:
            # Solution cluster: valid placements concentrate near green_ball.x
            # (empirical mean offset +0.42, range [-0.72, +0.87] over 20 solutions).
            x = float(np.clip(rng.normal(green_ball.x, 0.8), -4.5, 4.5))
        elif draw < 0.8:
            # Basket approach corridor: preserves coverage for seeds where the
            # valid placement is near the basket mouth rather than the green ball.
            x = float(np.clip(rng.normal(basket.x, 1.2), -4.5, 4.5))
        else:
            # Uniform fallback: preserves coverage for out-of-cluster seeds.
            x = rng.uniform(-4.5, 4.5)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("staircase")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None


# Geometric-decay analysis (2026-04-14): p=0.344 per variant with basket-centered Gaussian.
# Two-Gaussian mixture (green_ball 50% + basket 30% + uniform 20%) expected to raise p ~0.55
# by centering on the empirical solution cluster. k=25 retains <1 expected impossible per
# 10001 seeds at p=0.55; same max_variants is sufficient.
register_defaults("staircase", max_variants=25, n_attempts=500)
