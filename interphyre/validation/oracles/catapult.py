"""Targeted oracle for catapult.

Causal chain: red ball dropped onto or near the catapult arm (right of pivot_ball)
adds torque that rotates the arm, launching green_ball from the left tip rightward
into the basket where blue_ball rests.

Two distinct mechanisms observed in bundle data (6,000-seed partial bundle, 1,541 valid):

Mechanism 1 — catapult throw (Zone A, 74.4% of solutions):
  Red ball drops from high above the left/center board (x ≤ 0.2, y ≥ arm_top+1.0),
  lands on the arm right of the pivot, rotates the arm, and launches the green ball.
  y_rel above arm_top: [0.52, 7.57], mean = 5.18 — high drops are required.

Mechanism 2 — basket destabilisation (Zone B, 25.5% of solutions):
  Red ball placed near the basket (x ∈ [1.97, 4.50], median ≈ basket_x ≈ 3.9),
  destabilises the basket or ejects the blue ball toward the still-stationary
  green ball. All right-side solutions have x > 1.97; zero solutions exist in
  x ∈ (0.2, 1.97].

Zone A (70% of attempts): x ∈ [−4.5, arm_right + 1.0 = 0.2], y ∈ [arm_top + 1.0, 4.5].
  Covers 74.4% of bundle solutions. arm_right is fixed at −0.80 for all seeds.
  Area ≈ 4.7 × (4.5 − arm_top − 1.0) ≈ 27 sq units (arm_top median = −2.28).

Zone B (30% of attempts): x ∈ [2.0, 4.5], y ∈ [arm_top + 0.5, 4.5].
  Covers 25.5% of solutions (basket-destabilisation mechanism).
  x_min_b = 2.0 hardcoded: all right-side solutions have x > 1.97.
  Prior x_min_b = arm_right = −0.80 wasted 52% of Zone B's x-range on [−0.80, 1.97]
  where zero solutions exist, reducing hit density by 2.1× (oracle_physics_audit 2026-04-12).
  Area ≈ 2.5 × (4.5 − arm_top − 0.5) ≈ 16 sq units — 2.1× denser than prior Zone B.

Bundle analysis (2026-04-12, 1,541 valid seeds from ~6,000 partial bundle):
- Zone A (x ≤ 0.2, y ≥ arm_top+1.0): 74.4% of solutions
- Zone B (x > 1.97): 25.5% of solutions
- Near-arm (y < arm_top+1.0): 1.2% — captured by Zone B y_min = arm_top+0.5

Note: ~25% valid rate despite correct zones is genuine geometric impossibility
(catapult throw requires precise arm/ledge geometry for 8-unit horizontal launch).
Increasing n_attempts = 200 and sweeping max_variants = 10 are required for full
bundle coverage — all 4,487 impossible seeds in current bundle are at variant=0 only.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_defaults, register_oracle, register_solver, Box2DEngine


@register_solver("catapult")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    gray_platform = level.objects["gray_platform"]

    # Sample radius independently: r∈[0.9,1.2] covers the solvable range (r<0.9 has
    # only 3.5% solvability due to insufficient torque; analysis: catapult_redesign_analysis.md).
    # The level file's red_ball.radius is a placeholder — place_action_objects overrides it.
    radius = rng.uniform(0.9, 1.2)

    arm_right = gray_platform.x + gray_platform.length / 2
    arm_top = gray_platform.y + gray_platform.thickness / 2

    # Zone A: left/center of board, well above the arm — covers 86.9% of solutions.
    # arm_right is -0.80 for all seeds (arm starts at MIN_X+0.2, length=4.0).
    x_max_a = float(np.clip(arm_right + 1.0, -4.5, 4.5))  # always 0.2
    y_min_a = float(np.clip(arm_top + 1.0, -4.5, 4.5))

    # Zone B: basket-destabilisation mechanism — covers 25.5% of solutions.
    # All right-side solutions have x > 1.97 (near basket at x ≈ 3.7).
    # x_min_b = 2.0 hardcoded: prior x_min_b = arm_right = -0.80 wasted 52% of
    # Zone B's x-range on [-0.80, 1.97] which contains zero valid solutions.
    # Narrowing to [2.0, 4.5] gives 2.1× higher density for the basket region.
    x_min_b = 2.0  # hardcoded: basket x ∈ [3.2, 4.3]; all right-side solutions x > 1.97
    y_min_b = float(np.clip(arm_top + 0.5, -4.5, 4.5))

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        if i % 10 < 7:
            # Zone A (70%): high drops from left/center board — primary mechanism.
            x = rng.uniform(-4.5, x_max_a)
            y = rng.uniform(y_min_a, 4.5)
        else:
            # Zone B (30%): basket-destabilisation mechanism.
            # x ∈ [2.0, 4.5] = 2.5 units; 2.1× denser than prior [-0.80, 4.5] Zone B.
            x = rng.uniform(x_min_b, 4.5)
            y = rng.uniform(y_min_b, 4.5)

        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("catapult")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None


# oracle_steps audit (2026-04-14): v3 bundle (5192/10001=51.9%) used oracle_steps=500.
# Full-board test with oracle_steps=1000 recovered 8/20 = 40% of impossible seeds.
# 5/8 of those recoveries FAILED at oracle_steps=500 — the trajectory simply needed
# more simulation time for green_ball to reach the basket (catapult throw takes 8-17s
# simulated; 500 steps × (1/60)s = 8.3s is insufficient for many trajectories).
# Fix: oracle_steps must be raised to 1000 in the bundle script (--oracle-steps 1000).
# Expected post-v4: ~70-75% valid (40%+ of 4809 false negatives recovered).
register_defaults("catapult", max_variants=20, n_attempts=500)
