"""Targeted oracle for pinball_machine.

Causal chain: green_ball starts near the top (y ≈ 3.6). It must reach
purple_floor at the bottom, navigating through zigzag star obstacles. Drop
red_ball near the green_ball to start it moving; the star chains are sparse
enough that a direct push succeeds often enough across seeds.

Fix (this version): The original oracle used y ∈ [gb.y + 0.2, gb.y + 2.0].
With gb.y = 3.6 (constant), y_max = clip(5.6) = 4.5, giving y range =
[3.8, 4.5] — only 0.7 units above gb. By analogy with locust_swarm (same
causal structure), a minority of seeds have valid placements at y < gb.y
that the oracle never samples.

Fix: Two sampling zones (cycled per attempt):

Zone A (75% of attempts): x near green_ball ± 2.0, y in [gb.y + 0.2, 4.5].
  Standard mechanism: red ball drops from just above green_ball.

Zone B (25% of attempts): x near green_ball ± 2.0, full-board y [-4.5, 4.5].
  Catches seeds with valid placements below green_ball level.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, register_solver, Box2DEngine


@register_solver("pinball_machine")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    x_min = float(np.clip(green_ball.x - 2.0, -4.5, 4.5))
    x_max = float(np.clip(green_ball.x + 2.0, -4.5, 4.5))
    y_min_a = float(np.clip(green_ball.y + 0.2, -4.5, 4.5))

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        if i % 4 < 3:
            # Zone A (75%): drop from just above green_ball — standard mechanism.
            y = rng.uniform(y_min_a, 4.5)
        else:
            # Zone B (25%): full-board y for seeds with low-y solutions.
            y = rng.uniform(-4.5, 4.5)

        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("pinball_machine")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
