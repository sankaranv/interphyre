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
  Covers 86.9% of bundle solutions. arm_right is fixed at −0.80, so Zone A is
  always x ∈ [−4.5, 0.2], y ∈ [arm_top + 1.0, 4.5].

Zone B (30% of attempts): x ∈ [arm_right, 4.5], y ∈ [arm_top + 0.5, 4.5].
  Targeted at the 13.1% of solutions with x > 0.2 (right-side mechanism) and
  those with y slightly below arm_top + 1.0.  Previously full-board (81 sq units);
  now restricted to the right half where the outlier solutions cluster (4.3 × variable
  height ≈ 15–20 sq units), giving 4–5× better sampling density for those seeds.

Bundle analysis (2026-04-12, 1274 valid seeds):
- arm_right fixed at -0.80 for all seeds (arm length 4.0, always starts at MIN_X+0.2)
- 86.9% of solutions in Zone A (x ≤ 0.2, y ≥ arm_top+1.0)
- 7.6% of solutions: x > 0.2 only (right side) → now covered by Zone B's x range
- 4.3% of solutions: y < arm_top+1.0 (near-arm) → now covered by Zone B's y = arm_top+0.5
- 1.2% of solutions: both x > 0.2 and y < arm_top+1.0 → covered by Zone B
- Low overall valid rate (7.5%) despite correct zone design is due to sparse solution
  space — n_attempts=200 recommended for bundle generation to improve hit rate.
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

    # Zone A: left/center of board, well above the arm — covers 86.9% of solutions.
    # arm_right is -0.80 for all seeds (arm starts at MIN_X+0.2, length=4.0).
    x_max_a = float(np.clip(arm_right + 1.0, -4.5, 4.5))  # always 0.2
    y_min_a = float(np.clip(arm_top + 1.0, -4.5, 4.5))

    # Zone B: right side of board and near-arm region — covers 13.1% of outlier solutions.
    # Focused on x > arm_right (right side where 7.6% of solutions cluster) and
    # y ≥ arm_top+0.5 (covers near-arm solutions with y_rel slightly below 1.0).
    x_min_b = float(np.clip(arm_right, -4.5, 4.5))  # always -0.80
    y_min_b = float(np.clip(arm_top + 0.5, -4.5, 4.5))

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        if i % 10 < 7:
            # Zone A (70%): high drops from left/center board — primary mechanism.
            x = rng.uniform(-4.5, x_max_a)
            y = rng.uniform(y_min_a, 4.5)
        else:
            # Zone B (30%): right-side and near-arm fallback.
            # Previously full-board (81 sq units); now 4.3 × variable height ≈ 15–20 sq units.
            x = rng.uniform(x_min_b, 4.5)
            y = rng.uniform(y_min_b, 4.5)

        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("catapult")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
