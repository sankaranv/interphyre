"""Targeted oracle for straight_face.

Causal chain: green_ball (top, ball_x) must land on purple_pad (target_x, floor).
Gray_ball sits directly below at the same x. The red_ball acts as a deflector:
placed between ball_x and target_x, it redirects the falling stack horizontally
toward the pad.

Fix (this version): The original oracle used y_min = gray_ball.y − 1.5, which
for gray_ball.y ≈ 2.5 gave y_min = 1.0 — cutting off the lower two-thirds of
the board. Full-board sweeps confirmed valid placements reach down to y ≈ −3.5
(deflecting the ball after it passes the gray ball level). Fix: full-board y
from −4.5 to green_ball.y + 0.5, and full-board x. Note: ~40% of impossible
seeds are genuinely impossible due to extreme lateral separation between
green_ball and pad, and are unaffected by this fix.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_defaults, register_oracle, register_solver, Box2DEngine


@register_solver("straight_face")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Full-board x and y: valid deflections exist at any lateral position and
    # anywhere below the green ball, including well below the gray ball level.
    # The original corridor-only x and gray_ball-anchored y floor both cut off
    # large regions of valid placements confirmed by full-board sweeps.
    y_min = -4.5
    y_max = float(np.clip(green_ball.y + 0.5, -4.5, 4.5))

    engine = Box2DEngine(level=level, config=config)
    for _ in range(n_attempts):
        x = rng.uniform(-4.5, 4.5)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("straight_face")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None


# Geometric-decay analysis (2026-04-14): p=0.503 per variant, model(k=20)=0.0 impossible.
# k=20 reduces expected impossible from 9 (k=10) to <1 per 10001 seeds.
register_defaults("straight_face", max_variants=20, n_attempts=100)
