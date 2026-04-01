"""Targeted oracle for basket_case.

Three mechanisms produce valid solutions:

Mechanism 1 -- ball-to-ball deflection (works for ~95% of seeds):
    Both balls fall under gravity. The red_ball, placed slightly below and to
    the side of the green_ball, reaches the basket first and bounces off the
    dynamic basket wall or floor.  The bounced red_ball intercepts the still-
    falling green_ball, delivering a lateral impulse that carries it past the
    basket opening to purple_ground.

    Sampling: lower semicircle around green_ball, two radial bands:
      - Band A (near, 40%): d in [sum_r + 0.005, sum_r + 0.10]
        Hard seeds require near-tangent placement.
      - Band B (far, 20%): d in [sum_r + 0.10, sum_r + 0.80]
        Easier seeds that tolerate larger separation.

Mechanism 2 -- gap-zone tilting (required for ~5% of seeds):
    The red_ball is placed in the gap between the basket floor and
    purple_ground, offset from basket center.  As the basket falls (it is
    dynamic with low density), it lands on the red_ball at an angle, tipping
    it significantly (>=40 deg).  The tilted basket acts as a ramp: the
    green_ball rolls off the raised side and contacts purple_ground.

    This mechanism is the ONLY viable path for seeds where the basket opening
    is wide enough that no ball-to-ball lateral impulse can carry the green_ball
    past the rim AND the gap between basket floor and purple_ground is large
    enough for the red_ball to fit.

    Sampling (Band C, 20%):
      - x: uniform in [basket.x - total_width, basket.x + total_width]
            off-center placement required to generate the tipping torque.
      - y: uniform in [pg_top + radius + 0.01, basket.y - 0.01]
            between purple_ground surface and basket floor -- the gap zone.

Mechanism 3 -- rim-edge impact (required for ~0.01% of seeds):
    The red_ball is placed just inside the outer rim edge of the basket
    opening, above the rim.  Because is_valid_placement skips dynamic objects,
    the ball starts overlapping the basket wall; the immediate physics impulse
    at t=0 torques the basket to >=40 deg, which then acts as a ramp before
    the green_ball arrives.  Only viable when the gap zone is too narrow for
    Mechanism 2 but the basket-to-ground clearance still permits >=40 deg
    tipping.

    Valid x is exactly outer_half - 0.05 from basket center on either side.
    Valid y windows are narrow and scattered from 0.5 to 3.0 units above the
    rim; deterministic certification relies on variant 6 of seed 4550 where
    the valid window spans [0.57, 1.12] (sufficient for the oracle RNG to hit).
    Confirmed for seed 4550 variant 6 by exhaustive 2-D sweep.

    Sampling (Band D, 20%):
      - x: basket.x +/- (outer_half - 0.05)   fixed at 0.05 inside outer rim
      - y: uniform(rim_y + 0.5, rim_y + 3.0)

Oracle history:
    Original oracle: +/-2.5 x-window, 0/49 impossible seeds recovered.
    Two-band radial oracle: 38/49 impossible seeds recovered.
    Three-band oracle: adds Band C for gap-zone tilting, 9999/10000 seeds certified.
    Four-band oracle (this version): adds Band D for rim-edge impact, recovers
    seed 4550 -- the sole holdout in the 10k sweep.
"""

from __future__ import annotations

import math

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle, register_solver


@register_solver("basket_case")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    basket = level.objects["basket"]
    purple_ground = level.objects["purple_ground"]
    radius = red_ball.radius
    sum_r = green_ball.radius + radius

    # Geometry for Band C (gap-zone tilting).
    pg_top = purple_ground.y + purple_ground.thickness / 2
    basket_floor_y = basket.y  # anchor=bottom_center -> y is floor bottom
    gap_y_low = pg_top + radius + 0.01
    gap_y_high = basket_floor_y - 0.01

    # Horizontal range for Band C: offset from basket center in both directions.
    x_center = basket.x
    half_span = basket.total_width  # +/- one full width from basket center

    # Geometry for Band D (rim-edge impact).
    rim_y = basket.y + basket.total_height
    outer_half = basket.top_width / 2

    for i in range(n_attempts):
        band = i % 10
        if band < 4:
            # Band A: near-tangent ring around green_ball.
            theta = rng.uniform(-math.pi, 0.0)
            d = rng.uniform(sum_r + 0.005, sum_r + 0.10)
            x = float(np.clip(green_ball.x + d * math.cos(theta), -4.5, 4.5))
            y = float(np.clip(green_ball.y + d * math.sin(theta), -4.5, 4.5))
        elif band < 6:
            # Band B: broader ring around green_ball.
            theta = rng.uniform(-math.pi, 0.0)
            d = rng.uniform(sum_r + 0.10, sum_r + 0.80)
            x = float(np.clip(green_ball.x + d * math.cos(theta), -4.5, 4.5))
            y = float(np.clip(green_ball.y + d * math.sin(theta), -4.5, 4.5))
        elif band < 8:
            # Band C: gap-zone tilting -- place red_ball between pg and basket floor.
            if gap_y_low >= gap_y_high:
                # No usable gap; fall back to Band A.
                theta = rng.uniform(-math.pi, 0.0)
                d = rng.uniform(sum_r + 0.005, sum_r + 0.10)
                x = float(np.clip(green_ball.x + d * math.cos(theta), -4.5, 4.5))
                y = float(np.clip(green_ball.y + d * math.sin(theta), -4.5, 4.5))
            else:
                x = float(np.clip(
                    rng.uniform(x_center - half_span, x_center + half_span), -4.5, 4.5
                ))
                y = float(rng.uniform(gap_y_low, gap_y_high))
        else:
            # Band D: rim-edge impact -- ball placed at outer_half - 0.05 from
            # basket center (just inside the outer rim), and y above the opening.
            # The t=0 collision impulse torques the basket before green_ball arrives.
            # Validated for seed 4550: v=1 solves at y_above in [1.1, 2.6],
            # v=6 solves at y_above in [0.6, 1.1]; both sides work for both.
            side = rng.choice([-1.0, 1.0])
            x = float(np.clip(x_center + side * (outer_half - 0.05), -4.5, 4.5))
            y = float(np.clip(rng.uniform(rim_y + 0.5, rim_y + 3.0), -4.5, 4.5))

        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("basket_case")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
