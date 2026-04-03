"""Targeted oracle for just_a_nudge.

Causal chain: green_ball sits on a platform. The basket at the bottom must be
positioned under the green_ball's fall trajectory so green_ball contacts blue_ball.

Prior oracle (invalid): sampled from outside basket walls to push the basket
laterally. Previous analysis claimed no valid placements existed and labeled
this an open design issue. The basket-push approach was correctly exhausted —
a lateral push on the basket cannot generate the ~0.5–1.5 unit displacement
required. This conclusion was correct about the basket mechanism.

Sweep finding (2026-04-03): 10% of labeled-impossible seeds are solvable (3/30).
The oracle missed all valid placements because the CORRECT mechanism is different.

Valid mechanism (from sweep): The red ball knocks the green ball DIRECTLY OFF
THE PLATFORM. The basket does not move significantly; the green ball's launch
angle after being knocked changes its fall trajectory so it lands in the basket.
All 3 sweep solutions have red ball y ∈ [1.24, 2.59] (near the platform, NOT
near the basket at y ≈ −4.9). The x offsets from green_ball range ±3.27 units.

This level is genuinely hard: 90% of seeds are confirmed impossible at 40×40
resolution. The valid 10% of seeds have specific platform geometry where the
platform knocking angle naturally directs the green_ball toward the basket.

Fix: Sample near the green_ball on the platform (not the basket).

Zone A (70% of attempts): x ∈ [gb.x − 3.5, gb.x + 3.5], y ∈ [gb.y − 1.5, gb.y + 2.5].
  Covers all 3 sweep solutions (x offsets up to ±3.3, y offsets −1.5 to +0.9).

Zone B (30% of attempts): full-board x and y.
  Fallback for seeds where the valid placement is far from the platform.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, register_solver, Box2DEngine


@register_solver("just_a_nudge")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    x_min_a = float(np.clip(green_ball.x - 3.5, -4.5, 4.5))
    x_max_a = float(np.clip(green_ball.x + 3.5, -4.5, 4.5))
    y_min_a = float(np.clip(green_ball.y - 1.5, -4.5, 4.5))
    y_max_a = float(np.clip(green_ball.y + 2.5, -4.5, 4.5))

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        if i % 10 < 7:
            # Zone A (70%): near green_ball platform — direct knockoff mechanism.
            x = rng.uniform(x_min_a, x_max_a)
            y = rng.uniform(y_min_a, y_max_a)
        else:
            # Zone B (30%): full board fallback.
            x = rng.uniform(-4.5, 4.5)
            y = rng.uniform(-4.5, 4.5)

        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("just_a_nudge")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
