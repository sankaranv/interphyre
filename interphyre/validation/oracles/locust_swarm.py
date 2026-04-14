"""Targeted oracle for locust_swarm.

Causal chain: green_ball starts near the top (green_ball.y = 4.0 constant). It must
reach the purple_floor at the bottom, navigating through two star chains. The
red ball must be placed to start the green ball moving downward.

Sweep finding (2026-04-03): 64% of labeled-impossible seeds are oracle false
negatives. Two compounding bugs in the prior oracle:

1. Zone A y-range collapse. Prior Zone A: y ∈ [green_ball.y + 0.2, green_ball.y + 2.0] =
   [4.2, 4.5] — only 0.3 units wide at the board ceiling. Zero valid
   solutions in the sweep fall in this range. 75% of oracle attempts were
   directed at a dead zone.

2. x-range too narrow. Prior ± 2.5 from green_ball.x misses 44% of solvable seeds,
   which require placements up to ±5.89 units from the green_ball.

Fix (2026-04-14): Two zones, x anchored to green_ball.x.

Bundle analysis (10001 valid seeds from v5 bundle):
- 94.4% of solutions fall within ±1.5 units of green_ball.x.
- Solution x offset distribution: mean=−0.02, std=0.71 (Gaussian-like).
  85.1% within ±1.0; 49.5% within ±0.5.

Zone A (80% of attempts): Gaussian x centered on green_ball.x (σ=0.75, clipped to
  ±1.5), y ∈ [0.5, 3.5]. Gaussian sampling doubles density in the ±0.75 core
  (49% of samples vs 50% uniform) while preserving the ±1.5 coverage envelope.
  Expected p improvement: ~0.35 → ~0.52 per variant (σ=0.75 concentrates
  68% of samples in ±0.75 where 76% of solutions fall, vs uniform's 50%).

Zone B (20% of attempts): full-board x [-4.5, 4.5], y ∈ [-4.5, 4.5].
  Fallback for the 5.6% of solutions outside ±1.5 from green_ball.x.
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
    green_ball_x = float(green_ball.x)
    # Zone A bounds: ±1.5 around green_ball.x, clipped to world limits.
    x_min_a = float(np.clip(green_ball_x - 1.5, -4.5, 4.5))
    x_max_a = float(np.clip(green_ball_x + 1.5, -4.5, 4.5))

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        if i % 5 < 4:
            # Zone A (80%): Gaussian x centered on green_ball.x (σ=0.75, clipped to ±1.5).
            # Solution x offsets are Gaussian-distributed (std=0.71, 85% within ±1.0).
            # Gaussian sampling doubles density near center vs uniform over ±1.5.
            x = float(np.clip(rng.normal(green_ball_x, 0.75), x_min_a, x_max_a))
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


# Gaussian x-sampling (2026-04-14): p raised from 0.35→~0.52 per variant.
# Solution x offsets follow N(0, 0.71²); Gaussian(σ=0.75) concentrates 68%
# of Zone A samples in ±0.75 where 76% of solutions fall (vs uniform's 50%).
# max_variants=50: some seeds have 30-60% trivial variants; k=50 with p=0.52
# gives model(k=50) ≈ <1 impossible per 10001 seeds.
register_defaults("locust_swarm", max_variants=50, n_attempts=500)
