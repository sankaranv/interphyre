"""Targeted oracle for the_cradle.

Causal chain: green_ball rests in a V-shaped cradle formed by two short bars
(left_holder at 175°, right_holder at 5°) meeting at the junction vertex below
the green_ball. The oracle must dislodge green_ball from the V so it falls to
the purple_floor below.

Prior oracle design (invalid): placed red_ball using a near-tangent lateral
approach from the side of green_ball (x_offset ∈ [0.7, 0.99] × sum_r, y just
above tangent). This was the only approach attempted and was empirically
exhausted with zero success across seeds 0–4.

Sweep finding (2026-04-03): 83% of labeled-impossible seeds are oracle false
negatives. The prior oracle never tried placing the red ball ABOVE the cradle
and dropping it from high on the board.

All 25 seeds solved by the full-board grid sweep have winning positions at
y ∈ [2.59, 4.40] — well above the cradle and the green_ball (which sits at
y ∈ [-3, 0] depending on the seed). The mechanism is a top-down drop: the red
ball falls from high on the board, impacts the green_ball or the holder bars,
and dislodges the green_ball from the V so it falls to the purple_floor.

Dislodging mechanism (2026-04-14): direct center hits settle the green_ball
deeper in the V; dislodging requires the red ball to hit laterally, within
sum_of_radii ≈ 1.0 of gb.x horizontally. The original Zone A (±3.0 from gb.x,
6-unit wide) had very low solution density because the outer strips
[gb.x−3.0, gb.x−1.2] and [gb.x+1.2, gb.x+3.0] contribute almost no solutions.
Estimated solution-strip area ≈ 0.07 sq units in 12 sq units → 0.46% per attempt.

Empirical solution geometry (sweep, 25 solved seeds):
- y ∈ [2.59, 4.40] — all solutions in top 60% of board height
- x ∈ [-2.37, 3.50] — spread across most of the board width

Zone A (75% of attempts): x ∈ [gb.x − 1.5, gb.x + 1.5], y ∈ [2.5, 4.5].
  Narrowed to ±1.5 from gb.x to concentrate sampling in the lateral-contact
  strip (sum_of_radii max ≈ 1.1), roughly doubling solution density vs ±3.0.

Zone B (25% of attempts): x ∈ [gb.x − 3.0, gb.x + 3.0], full y range.
  Wider fallback (±3.0 from gb.x, not full board) for seeds where geometry
  shifts the contact zone. Sweep shows solutions rarely beyond ±3 from gb.x.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_defaults, register_oracle, register_solver, Box2DEngine


@register_solver("the_cradle")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    x_min_a = float(np.clip(green_ball.x - 1.5, -4.5, 4.5))
    x_max_a = float(np.clip(green_ball.x + 1.5, -4.5, 4.5))
    x_min_b = float(np.clip(green_ball.x - 3.0, -4.5, 4.5))
    x_max_b = float(np.clip(green_ball.x + 3.0, -4.5, 4.5))

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        if i % 4 < 3:
            # Zone A (75%): narrow lateral-contact strip above the cradle.
            # ±1.5 from gb.x keeps sampling within the dislodging contact zone
            # (sum_of_radii max ≈ 1.1) with margin, roughly doubling density vs ±3.0.
            x = rng.uniform(x_min_a, x_max_a)
            y = rng.uniform(2.5, 4.5)
        else:
            # Zone B (25%): wider fallback (±3.0 from gb.x) for seeds with
            # shifted geometry; sweep shows solutions rarely beyond ±3 from gb.x.
            x = rng.uniform(x_min_b, x_max_b)
            y = rng.uniform(-4.5, 4.5)

        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("the_cradle")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None


# Geometric-decay analysis (2026-04-14): p≈0.37 per variant at 100 attempts (0.46%/attempt).
# Narrowed Zone A (±1.5 vs ±3.0) roughly doubles density → ~0.92%/attempt → p≈0.60 at 200 attempts.
# k=20 variants with p≈0.60 gives near-zero false-negative rate.
register_defaults("the_cradle", max_variants=20, n_attempts=200)
