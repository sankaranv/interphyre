"""Targeted oracle for catapult.

Causal chain: red ball dropped onto or near the catapult arm (right of pivot_ball)
adds torque that rotates the arm, launching green_ball from the left tip rightward
into the basket where blue_ball rests.

Two mechanisms observed in bundle data (v4 bundle, 8492/10001 = 84.9% valid):

Mechanism 1 — catapult throw (Zone A, ~94% of solutions):
  Red ball drops from above the arm (y ≥ arm_top+1.0), RIGHT of the pivot, rotates
  the arm, and launches the green ball. 100% of Zone A solutions land right of
  pivot_x (= arm_right − arm_length/2). The prior oracle sampled x ∈ [−4.5, arm_right+1]
  which wasted ~50% of Zone A x-samples left of pivot. Fix: x ∈ [pivot_x−0.5, arm_right+1].

Mechanism 2 — basket destabilisation (Zone B, ~6% of solutions):
  Red ball placed near the basket (x > 1.97, y above arm) destabilises the basket
  or ejects the blue ball. All right-side solutions have x > 1.97.

Zone A (70% of attempts): x ∈ [pivot_x − 0.5, arm_right + 1.0], y ∈ [arm_top + 1.0, 4.5].
  Width = 3.6 units (vs prior 6.2 units). 2× denser sampling of the valid x-region.
  arm_right ∈ [0.725, 1.225] with current level constraint (black_platform_x ∈ [−2.0, −1.5]).

Zone B (30% of attempts): x ∈ [2.0, 4.5], y ∈ [arm_top + 0.5, 4.5].
  x_min_b = 2.0 hardcoded: basket at x = 3.5; all right-side solutions x > 1.97.

oracle_steps audit (20-seed 15×15 grid sweep): 2/20 FNR = 10%. ~228/253 impossible seeds
in v5 bundle genuinely impossible (geometric impossibility, not oracle misses). Level
constraints applied in v5:
  - black_platform_x ∈ [−2.0, −1.5]: arm_right ≥ 0.725 (was −2.5; 75% of impossibility)
  - ledge_center_y ∈ [−4, −2.5]: eliminates high-basket geometry

Impossibility analysis (v5 bundle, 253 impossible seeds): No simple parameter bound
achieves 100% valid. Best single discriminator: arm_right (d=−0.47). Best combined:
arm_right − 0.5×basket_scale (d=−0.64, ratio=4.8 only at 6.7% coverage). Floating-basket
redesign (v6: ledge_center_x = arm_right + 2.5) was tested and showed no solvability
improvement (3.0% impossible vs 2.5% in v5). The impossibility arises from complex
non-linear trajectory physics — the feasibility boundary shifts when individual parameters
change. Accepted as design ceiling: ~2.5% of catapult seeds are genuinely impossible.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_defaults, register_oracle, register_solver, Box2DEngine


@register_solver("catapult")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    gray_platform = level.objects["gray_platform"]

    # Catapult throw + ballistic flight takes 8–17 simulated seconds.
    # Cap at config.max_steps: never certify solutions that exceed the user-visible
    # simulation window. Callers must pass oracle_steps = config.max_steps (1000) to
    # avoid missing solutions that complete in the 500–1000 step range.
    # oracle_steps=500 (8.3 s) truncates trajectories mid-flight;
    # full-board test at config.max_steps recovered 40% of false-negative impossible seeds.
    oracle_steps = min(oracle_steps, config.max_steps)

    # Sample radius independently: r∈[0.9,1.2] covers the solvable range (r<0.9 has
    # only 3.5% solvability due to insufficient torque.
    # The level file's red_ball.radius is a placeholder — place_action_objects overrides it.
    radius = rng.uniform(0.9, 1.2)

    arm_right = gray_platform.x + gray_platform.length / 2
    arm_top = gray_platform.y + gray_platform.thickness / 2

    # pivot_x: the catapult arm rotates around gray_ball, which sits at arm center.
    # arm_right = gray_platform center + length/2; pivot = center = arm_right - length/2.
    # 100% of Zone A solutions have x right of pivot (x > pivot_x); sampling the
    # left half of Zone A (x < pivot_x) yields zero solutions and wastes 50% of attempts.
    # Fix: Zone A x ∈ [pivot_x - 0.5, arm_right + 1.0] — 3.6 units vs 6.2 for the old range.
    # pivot_x = arm_right - gray_platform.length / 2 ≈ arm_right - 2.125.
    pivot_x = arm_right - gray_platform.length / 2
    x_min_a = float(np.clip(pivot_x - 0.5, -4.5, 4.5))  # 0.5-unit margin left of pivot
    x_max_a = float(np.clip(arm_right + 1.0, -4.5, 4.5))
    y_min_a = float(np.clip(arm_top + 1.0, -4.5, 4.5))

    # Zone B: basket-destabilisation mechanism — covers ~6% of solutions.
    # All right-side solutions have x > 1.97 (near basket at x = 3.5).
    x_min_b = 2.0  # hardcoded: basket x = 3.5; all right-side solutions x > 1.97
    y_min_b = float(np.clip(arm_top + 0.5, -4.5, 4.5))

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        if i % 10 < 7:
            # Zone A (70%): right-of-pivot drops — primary catapult throw mechanism.
            # x ∈ [pivot_x - 0.5, arm_right + 1.0] = 3.6 units; ~2× denser than old [-4.5, arm_right+1].
            x = rng.uniform(x_min_a, x_max_a)
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


# oracle_steps calibration: 500 steps (8.3 s simulated) truncates many trajectories.
# Full-board test with oracle_steps=1000 recovered 40% of false-negative impossible seeds —
# the catapult throw takes 8–17 s simulated; 500 steps is insufficient for many paths.
# oracle_steps must be 1000 in the bundle script (--oracle-steps 1000).
register_defaults("catapult", max_variants=20, n_attempts=500)
