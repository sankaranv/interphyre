"""Targeted oracle for marble_race.

Causal chain: left_beam (gray, dynamic) is a horizontal gate resting on two static
black balls. black_ball_2 sits near the LEFT end of the beam (acts as pivot).
black_ball_1 sits near the RIGHT end. Dropping red_ball on the outer right portion
of the beam — between black_ball_1 and the right edge — tips the beam clockwise
(right end down, left end up) around the left pivot. The raised left end opens the
path for green_ball (rolling down left_ramp_2) to pass along the beam and continue
via left_ramp_1 to the basket.

Empirical sweep (seeds 0-29, 50×12 grid) confirmed effective placement:
  x: [black_ball_1.x - 0.10, left_beam.right + 0.30]  (outer right arm past support)
  y: [left_beam.y + 0.15, min(left_beam.y + 2.5, ceiling_bottom - r - 0.05)]

Physics timing: the full chain (tip → green ball traverse + ramp sequence + basket
contact) requires ≥1000 physics steps (~8 s at 60 Hz). oracle_steps=500 misses ~75%
of solvable seeds. We override to a minimum of 1500 steps so that seeds with small-
radius red balls (which tip more slowly) are correctly classified as solvable.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle

# Minimum physics steps required for the causal chain to complete.
# 500-step oracle runs classify most marble_race seeds as "impossible" because
# the multi-ramp path (left_beam → left_ramp_1 → basket) needs ~1000-1500 steps.
_MIN_ORACLE_STEPS = 1500


@register_oracle("marble_race")
def oracle(level, config, n_attempts, oracle_steps, rng):
    left_beam = level.objects["left_beam"]
    black_ball_1 = level.objects["black_ball_1"]  # right support
    ceiling = level.objects["ceiling"]
    red_ball = level.objects["red_ball"]

    r = red_ball.radius

    # Right arm of left_beam: from just left of the right support to just past the
    # right edge. This is the only zone that generates clockwise tipping torque.
    x_min = np.clip(black_ball_1.x - 0.10, -4.5, 4.5)
    x_max = np.clip(left_beam.right + 0.30, -4.5, 4.5)

    # Drop height: above beam surface, but below the ceiling.
    ceiling_bottom = ceiling.y - ceiling.thickness / 2
    y_min = np.clip(left_beam.y + 0.15, -4.5, 4.5)
    y_max = float(np.clip(min(left_beam.y + 2.5, ceiling_bottom - r - 0.05), -4.5, 4.5))

    # Ensure the chain has enough time to complete even for slow-tipping seeds.
    effective_steps = max(oracle_steps, _MIN_ORACLE_STEPS)

    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt(level, config, [(x, y, r)], effective_steps):
            return True
    return False
