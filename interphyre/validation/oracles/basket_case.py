"""Targeted oracle for basket_case.

Causal chain: green_ball starts at basket_x and falls directly into the basket.
Success requires the green_ball to contact purple_ground. The red_ball is placed
just below-and-to-the-side of the green_ball so it falls into the basket area
first, bounces off the basket wall or floor, then contacts the green_ball in
flight and deflects it laterally past the basket opening.

Mechanism (traced from simulation): both balls fall under gravity. The red_ball,
starting slightly below the green_ball, reaches the basket first and bounces.
The bounced red_ball intercepts the still-falling green_ball, delivering a
lateral impulse that carries it past the basket opening to purple_ground.

Sampling geometry: every successful solution has initial distance ≈ sum_r to
1.5 × sum_r from green_ball, with x_offset within ±sum_r of green_ball.x and
y_offset always negative (below). The previous oracle sampled x over a ±2.5
window — 3–5× wider than the effective contact zone — wasting most attempts on
positions where the red_ball falls past the basket entirely.

Revised strategy — two-band radial sampling:

Analysis of hard seeds (those that fail at n_attempts=50 with uniform d) reveals
that many seeds only admit valid placements in a very tight ring d ∈ [sum_r+0.005,
sum_r+0.10].  Uniform sampling over d ∈ [sum_r+0.02, sum_r+0.6] places only ~3%
of attempts in this effective zone, making hard seeds unlikely to be found.

Two-band split:
  - Band A (near, 70% of attempts): d ∈ [sum_r + 0.005, sum_r + 0.10]
    Catches hard seeds that require near-tangent placement.
  - Band B (far, 30% of attempts): d ∈ [sum_r + 0.10, sum_r + 0.80]
    Catches easier seeds that tolerate larger separation.

Angle: uniformly sampled from the lower semicircle [-π, 0] in both bands,
ensuring red_ball starts below green_ball and reaches the basket first.

Coverage ceiling: seeds with valid theta windows ≤ 1–4° (e.g., seeds 354, 562)
require ~3000–7000 random attempts for 90% detection probability — impractical
for oracle use.  Five seeds (310, 445, 493, 657, 792) are confirmed truly
impossible across all 10 variants via exhaustive grid search.  These ten seeds
(five truly impossible + five with sub-1% detection probability per attempt)
represent a level-design limitation, not an oracle failure.
"""

from __future__ import annotations

import math

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, register_solver


@register_solver("basket_case")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius
    sum_r = green_ball.radius + radius

    for i in range(n_attempts):
        theta = rng.uniform(-math.pi, 0.0)
        # Two-band radial sampling: near-tangent (70%) vs broader separation (30%).
        # Hard seeds only admit solutions at d ≈ sum_r + 0.005–0.10; the near band
        # concentrates most attempts there.
        if i % 10 < 7:
            d = rng.uniform(sum_r + 0.005, sum_r + 0.10)
        else:
            d = rng.uniform(sum_r + 0.10, sum_r + 0.80)
        x = float(np.clip(green_ball.x + d * math.cos(theta), -4.5, 4.5))
        y = float(np.clip(green_ball.y + d * math.sin(theta), -4.5, 4.5))
        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("basket_case")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
