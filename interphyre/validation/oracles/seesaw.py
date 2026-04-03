"""Targeted oracle for seesaw.

Causal chain: green_ball starts near the top (y~4.0) at a position aligned with
the beam edge. It falls toward the blue_beam. The red_ball should be placed near
the green_ball to guide it precisely onto the beam span.

Fix (this version): The original oracle used y ∈ [gb.y − 0.5, gb.y + 1.0] =
[3.5, 4.5]. Full-board sweeps of impossible-only seeds confirmed that valid
placements exist throughout the board — some seeds are solved by placements at
y ≈ −3.0 to +2.5, which are entirely outside the original oracle range. These
seeds were incorrectly labelled impossible due to y-range truncation.

Fix: Two sampling zones (cycled per attempt):

Zone A (50% of attempts): beam-intersection x logic, y in [gb.y − 0.5, 4.5].
  Covers seeds solved near the green_ball level, preserving the existing high
  success rate for those seeds.

Zone B (50% of attempts): full-board x and y [-4.5, 4.5].
  Covers seeds where valid placements are at low y (the ball falls past the
  beam and the red ball interacts at a lower point), confirmed by sweep.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, register_solver, Box2DEngine


@register_solver("seesaw")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    blue_beam = level.objects["blue_beam"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    beam_left = blue_beam.x - blue_beam.length / 2
    beam_right = blue_beam.x + blue_beam.length / 2

    # Zone A: beam-intersection x, y near green_ball.
    x_min_a = float(np.clip(max(beam_left - 0.5, green_ball.x - 1.5), -4.5, 4.5))
    x_max_a = float(np.clip(min(beam_right + 0.5, green_ball.x + 1.5), -4.5, 4.5))
    if x_min_a >= x_max_a:
        # Beam and green_ball too far apart — center on midpoint between them.
        cx = (green_ball.x + blue_beam.x) / 2
        x_min_a = float(np.clip(cx - 1.5, -4.5, 4.5))
        x_max_a = float(np.clip(cx + 1.5, -4.5, 4.5))
    y_min_a = float(np.clip(green_ball.y - 0.5, -4.5, 4.5))

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        if i % 2 == 0:
            # Zone A: near green_ball, within beam span.
            x = rng.uniform(x_min_a, x_max_a)
            y = rng.uniform(y_min_a, 4.5)
        else:
            # Zone B: full board — covers seeds where valid placements are at
            # low y (confirmed by sweep: solutions at y ≈ −3.0 to +2.5).
            x = rng.uniform(-4.5, 4.5)
            y = rng.uniform(-4.5, 4.5)

        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("seesaw")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
