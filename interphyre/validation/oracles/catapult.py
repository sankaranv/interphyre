"""Targeted oracle for catapult.

Causal chain: red ball dropped onto or near the catapult arm (right of pivot_ball)
adds torque that rotates the arm, launching green_ball from the left tip rightward
into the basket where blue_ball rests.

Prior oracle (invalid): sampled a narrow 0.29-unit band directly above the right
arm tip (y ∈ [arm_top + radius + 0.01, arm_top + radius + 0.30]). This was
claimed to cover all valid placements, with ~84% of seeds "genuinely impossible."

Sweep finding (2026-04-03): 60% false-negative rate (30/50 seeds solved by
full-board grid). The prior oracle docstring claim of 84% genuine impossibility
is refuted. Root cause: completely wrong causal model.

0/30 winning positions fell within the oracle's narrow band. The actual valid
mechanism involves **dropping from high above the arm** (y_rel median 5.08
units above arm_top), not barely above it. The ball falls far enough to deliver
sufficient momentum to trigger the catapult throw. The prior oracle sampled the
bottom 5% of the valid y range and missed 100% of solutions.

Empirical solution geometry (30 solved seeds):
- y_rel above arm_top: 0.65 to 6.78 units (median 5.08) — high drops required
- 53% cluster at x < −1.5 (left side of board, broadly distributed)
- 20% at x > 1.5 (right side); 27% mid-board
- 90% at y > 0 (upper board); 77% at y > 2
- arm_top does not distinguish solvable from impossible seeds

Fix:

Zone A (70% of attempts): x ∈ [−4.5, arm_right + 1.0], y ∈ [arm_top + 1.0, 4.5].
  Covers the 79% of winning positions that are on the left/center of the board
  and well above the arm.

Zone B (30% of attempts): full-board x and y.
  Fallback for the 20% of seeds with right-side winning positions, and for any
  seeds that require y close to arm_top or unusual geometry.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, register_solver, Box2DEngine


@register_solver("catapult")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    catapult_bar = level.objects["catapult_bar"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    arm_right = catapult_bar.x + catapult_bar.length / 2
    arm_top = catapult_bar.y + catapult_bar.thickness / 2

    # Zone A: left/center of board, well above the arm — covers 79% of sweep solutions.
    x_max_a = float(np.clip(arm_right + 1.0, -4.5, 4.5))
    y_min_a = float(np.clip(arm_top + 1.0, -4.5, 4.5))

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        if i % 10 < 7:
            # Zone A (70%): high drops from left/center board — primary mechanism.
            x = rng.uniform(-4.5, x_max_a)
            y = rng.uniform(y_min_a, 4.5)
        else:
            # Zone B (30%): full board — covers right-side solutions and outliers.
            x = rng.uniform(-4.5, 4.5)
            y = rng.uniform(-4.5, 4.5)

        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("catapult")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
