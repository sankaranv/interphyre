"""Targeted oracle for locust_swarm.

Causal chain: green_ball starts near the top (gb.y = 4.0 constant). It must
reach the purple_floor at the bottom, navigating through two star chains. The
red ball must be placed to start the green ball moving downward.

Sweep finding (2026-04-03): 64% of labeled-impossible seeds are oracle false
negatives. Two compounding bugs in the prior oracle:

1. Zone A y-range collapse. Prior Zone A: y ∈ [gb.y + 0.2, gb.y + 2.0] =
   [4.2, 4.5] — only 0.3 units wide at the board ceiling. Zero valid
   solutions in the sweep fall in this range. 75% of oracle attempts were
   directed at a dead zone.

2. x-range too narrow. Prior ± 2.5 from gb.x misses 44% of solvable seeds,
   which require placements up to ±5.89 units from the green_ball.

Fix (2026-04-14): Two zones, x anchored to green_ball.x.

Bundle analysis (valid seeds from prior bundle): 94.4% of solutions fall
within ±1.5 units of green_ball.x. Full-board x sampling wasted 66.7% of
the x budget on regions with near-zero solution density.

Zone A (80% of attempts): x ∈ [gb.x - 1.5, gb.x + 1.5] (clipped to world),
  y ∈ [0.5, 3.5]. Covers the central solution cluster.

Zone B (20% of attempts): full-board x [-4.5, 4.5], y ∈ [-4.5, 4.5].
  Fallback for the 5.6% of solutions outside ±1.5 from gb.x.

Expected p improvement: 0.143 → ~0.35; register_defaults k=20 gives
model(k=20) ≈ 3 impossible seeds (down from ~297 at k=10).
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


@register_solver("locust_swarm")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    green_ball = level.objects["green_ball"]
    gb_x = float(green_ball.x)
    # Zone A bounds: ±1.5 around green_ball.x, clipped to world limits.
    x_min_a = float(np.clip(gb_x - 1.5, -4.5, 4.5))
    x_max_a = float(np.clip(gb_x + 1.5, -4.5, 4.5))

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        if i % 5 < 4:
            # Zone A (80%): ±1.5 x-window around green_ball — 94.4% of bundle solutions.
            x = rng.uniform(x_min_a, x_max_a)
            y = rng.uniform(0.5, 3.5)
        else:
            # Zone B (20%): full-board fallback for outlier solutions.
            x = rng.uniform(-4.5, 4.5)
            y = rng.uniform(-4.5, 4.5)

        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("locust_swarm")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None


# Calibrated for p≈0.35 per variant (green_ball-centered Zone A).
# max_variants raised 20→50 (2026-04-14): seeds 4451 (found at v=47) and
# 8467 (found at v=40) needed >20 variants due to high trivial-variant rate.
# Some seeds have 30-60% trivial variants — need more non-trivial samples.
# model(k=50, p=0.35) ≈ <1 impossible seed out of 10001.
register_defaults("locust_swarm", max_variants=50, n_attempts=500)
