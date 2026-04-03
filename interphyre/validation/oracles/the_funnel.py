"""Targeted oracle for the_funnel.

Causal chain: green_ball starts at the top (MAX_Y). The funnel channels it
toward the center gap, then it falls to the floor. The purple_target is on one
side (left or right). A blocker bar deflects the ball away from the non-target
side. Drop red_ball near green_ball on the target side so it enters the funnel
correctly.

Fix (this version): green_ball.y = 4.70 (constant), causing y_min =
gb.y − 0.3 = 4.40 and y_max = clip(gb.y + 2.0) = 4.50 — a 0.1-unit strip.
Full-board sweeps of impossible-only seeds confirmed valid placements at
y ∈ [−4.5, +3.5] (e.g., seeds solved at y ≈ −4.0 to −3.0, and at y ≈ 3.0–3.5).
These were silently dropped because the oracle never sampled below y = 4.40.

Fix: Two sampling zones (cycled across attempts):

Zone A (60% of attempts): target-biased x, y in [4.35, 4.5].
  Covers the majority of seeds where the green_ball enters the funnel from the
  very top — standard mechanism, preserving existing high success rate.

Zone B (40% of attempts): target-biased x, full-board y [-4.5, 4.5].
  Covers seeds where valid placements are at low y (confirmed by sweep).
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, register_solver, Box2DEngine


@register_solver("the_funnel")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    purple_target = level.objects["purple_target"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Target-biased x center: 70% weight toward target, 30% toward green_ball.
    # Stronger bias than the original 50/50 since the ball must enter the funnel
    # on the correct side regardless of where green_ball starts.
    target_cx = (purple_target.left + purple_target.right) / 2
    cx = 0.3 * green_ball.x + 0.7 * target_cx
    x_min = float(np.clip(cx - 2.0, -4.5, 4.5))
    x_max = float(np.clip(cx + 2.0, -4.5, 4.5))

    # Zone A: y near top of board — standard mechanism (green_ball near y=4.7).
    y_min_a = float(np.clip(green_ball.y - 0.5, -4.5, 4.5))

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        if i % 5 < 3:
            # Zone A (60%): y near green_ball.y, standard funnel entry.
            y = rng.uniform(y_min_a, 4.5)
        else:
            # Zone B (40%): full-board y — covers seeds with low-y solutions
            # (confirmed by sweep: hits at y ≈ −4.4 to +3.5).
            y = rng.uniform(-4.5, 4.5)

        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("the_funnel")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
