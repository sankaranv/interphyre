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

    When Band A's y range is narrower than 1.0 units (near-ceiling green_ball,
    gb.y > ~3.5), Band A is skipped entirely and all 70% of those attempts are
    redirected to Band B. Full-board sweep of the 3 impossible seeds in the 10k
    run (1328, 2917, 7667) confirmed gb.y ∈ [3.1, 3.9] and hits distributed
    across the full board, not concentrated above the ball. A 0.6-unit Band A
    captures only ~7% of hits and yields ~13% per-variant success; Band B at
    100% of attempts yields ~60%, recovering all 3 seeds.

Band B (30% of attempts): approach from below.
    x in [cx - 2, cx + 2]  (same horizontal range as Band A).
    y in [-4.5, green_ball.y - 0.2].
    Required for seeds where the green_ball is near the top of the board and
    the above-approach collapses to a sliver (< 1.0 units of y range).  In
    these geometries a ball placed below and between the basket/wall delivers
    a lateral impulse through a different causal chain.  Empirically confirmed
    for seed 40 where Band A's y range is [4.05, 4.50] (0.45 units) but valid
    hits cluster at y in [-3.6, +1.1].

Oracle history:
    Original oracle: single band above green_ball, 997/1000 seeds certified.
    Two-band oracle: adds Band B below-green-ball, recovers seed 40.
    Near-ceiling fix (this version): redirect Band A attempts to Band B when
    Band A height < 1.0 units, recovering seeds 1328/2917/7667 (all had
    gb.y ∈ [3.1, 3.9] and near-zero Band A hit density in 10k run).
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_defaults, register_oracle, register_solver, Box2DEngine


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

    # Redirect Band A to Band B when the above-ball zone is too narrow to be
    # useful.  Full-board sweeps of the 3 impossible seeds in the 10k run showed
    # that near-ceiling seeds (gb.y > ~3.5) have hits spread across the full
    # board — not concentrated above the ball — making the collapsed Band A
    # (~0.6 unit y range) nearly worthless at only ~13% per-variant success.
    band_a_height = y_max_a - y_min_a
    use_band_a = band_a_height >= 1.0

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        if i % 10 < 7:
            # Band A: drop above (or Band B if Band A is near-ceiling collapsed).
            if use_band_a:
                y = rng.uniform(y_min_a, y_max_a)
            else:
                y = rng.uniform(-4.5, y_max_b)
        else:
            # Band B: approach from below.
            y = rng.uniform(-4.5, y_max_b)

        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("off_the_rails")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None


# Geometric-decay analysis (2026-04-14): p=0.380 per variant, model(k=20)=0.7 impossible.
# k=20 reduces expected impossible from 84 (k=10) to <1 per 10001 seeds.
register_defaults("off_the_rails", max_variants=20, n_attempts=100)
