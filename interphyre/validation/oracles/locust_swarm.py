"""Targeted oracle for locust_swarm.

Causal chain: green_ball starts near the top. It must reach the purple_floor at
the bottom, navigating through two star chains. Drop red_ball near the green_ball
to start it moving downward; the star chains are sparse enough that a direct push
succeeds often enough across seeds.

Fix (this version): The original oracle used y ∈ [gb.y + 0.2, gb.y + 2.0].
With gb.y = 4.0 (constant), y range = [4.2, 4.5] — only 0.3 units. Full-board
sweeps confirmed a minority of impossible seeds (~1/8 tested) have valid
placements at y ≈ 1.2–2.1 that the oracle never samples. Most impossible seeds
are genuinely impossible (dense star chains block all paths).

Fix: Two sampling zones (cycled per attempt):

Zone A (75% of attempts): x near green_ball ± 2.5, y in [4.2, 4.5].
  Standard mechanism: red ball drops from just above green_ball.

Zone B (25% of attempts): x near green_ball ± 2.5, full-board y [-4.5, 4.5].
  Catches rare seeds with valid placements below green_ball level.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, register_solver, Box2DEngine


@register_solver("locust_swarm")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Slightly wider x than original (±2.5 instead of ±2.0) to cover valid
    # solutions with large lateral offsets from green_ball.
    x_min = float(np.clip(green_ball.x - 2.5, -4.5, 4.5))
    x_max = float(np.clip(green_ball.x + 2.5, -4.5, 4.5))
    y_min_a = float(np.clip(green_ball.y + 0.2, -4.5, 4.5))
    y_max_a = float(np.clip(green_ball.y + 2.0, -4.5, 4.5))

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        if i % 4 < 3:
            # Zone A (75%): drop from just above green_ball — standard mechanism.
            y = rng.uniform(y_min_a, y_max_a)
        else:
            # Zone B (25%): full-board y for rare seeds with low-y solutions.
            y = rng.uniform(-4.5, 4.5)

        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("locust_swarm")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
