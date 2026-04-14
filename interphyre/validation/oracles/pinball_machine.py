"""Targeted oracle for pinball_machine.

Causal chain: green_ball starts near the top (gb.y = 4.0 constant). It must
reach the purple_floor at the bottom, navigating through zigzag star obstacles.
The red ball is placed below the green ball, which then falls and the collision
helps navigate through the stars.

Sweep finding (2026-04-03): 70% of labeled-impossible seeds are oracle false
negatives. Two compounding bugs in the prior oracle:

1. Zone A y-range collapse. Prior Zone A: y ∈ [gb.y + 0.2, 4.5] =
   [4.2, 4.5] — only 0.3 units wide at the board ceiling. Zero valid
   solutions in the sweep fall in this range. 75% of oracle attempts were
   directed at a dead zone.

2. x-range too narrow. Prior ± 2.0 from gb.x misses 17% of solvable seeds
   (winning positions up to 3.33 units from gb.x). Widening to ± 3.5 covers
   all 35 seeds solved in the sweep.

Empirical solution geometry (sweep, 35 solved seeds):
- y ∈ [-0.56, 3.50]; 68.6% at y ∈ [2.5, 3.5] (red ball 0.5–1.5 units below
  green ball, nudges it downward through the star field)
- |x − gb.x| ≤ 3.5 covers all 35 seeds

Fix:

Zone A (70% of attempts): x ∈ [gb.x − 3.5, gb.x + 3.5], y ∈ [1.5, 3.8].
  Covers the main cluster (68.6% of solutions at y ∈ [2.5, 3.5]).

Zone B (30% of attempts): x ∈ [gb.x − 3.5, gb.x + 3.5], full-board y.
  Covers the minority of seeds with very low y (y < 0) or other mechanisms.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_defaults, register_oracle, register_solver, Box2DEngine


@register_solver("pinball_machine")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    x_min = float(np.clip(green_ball.x - 3.5, -4.5, 4.5))
    x_max = float(np.clip(green_ball.x + 3.5, -4.5, 4.5))

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        if i % 10 < 7:
            # Zone A (70%): main cluster — red ball 0.5–2.5 units below green ball.
            y = rng.uniform(1.5, 3.8)
        else:
            # Zone B (30%): full-board y for seeds with low or unusual solutions.
            y = rng.uniform(-4.5, 4.5)

        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("pinball_machine")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None


# Geometric-decay analysis (2026-04-14): p=0.332 per variant, model(k=25)=0.3 impossible.
# k=25 reduces expected impossible from 176 (k=10) to <1 per 10001 seeds.
register_defaults("pinball_machine", max_variants=25, n_attempts=200)
