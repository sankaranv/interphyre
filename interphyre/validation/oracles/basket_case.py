"""Targeted oracle for basket_case.

Two mechanisms produce valid solutions (both confirmed by simulation trace):

Mechanism 1 — ball-to-ball deflection (works for ~95% of seeds):
    Both balls fall under gravity. The red_ball, placed slightly below and to
    the side of the green_ball, reaches the basket first and bounces off the
    dynamic basket wall or floor.  The bounced red_ball intercepts the still-
    falling green_ball, delivering a lateral impulse that carries it past the
    basket opening to purple_ground.

    Sampling: lower semicircle around green_ball, two radial bands:
      - Band A (near, 40%): d ∈ [sum_r + 0.005, sum_r + 0.10]
        Hard seeds require near-tangent placement.
      - Band B (far, 20%): d ∈ [sum_r + 0.10, sum_r + 0.80]
        Easier seeds that tolerate larger separation.

Mechanism 2 — basket-tilting (required for ~5% of seeds):
    The red_ball is placed in the gap between the basket floor and
    purple_ground, offset from basket center.  As the basket falls (it is
    dynamic with low density), it lands on the red_ball at an angle, tipping
    it significantly (≥40°).  The tilted basket acts as a ramp: the green_ball
    rolls off the raised side and contacts purple_ground.

    This mechanism is the ONLY viable path for seeds where the basket opening
    is wide enough that no ball-to-ball lateral impulse can carry the green_ball
    past the rim.

    Sampling (Band C, 40%):
      - x: uniform in [basket.x - total_width, basket.x + total_width]
            off-center placement required to generate the tipping torque.
      - y: uniform in [pg_top + radius + 0.01, basket.y - 0.01]
            between purple_ground surface and basket floor — the gap zone.

    Note: valid positions also exist at higher y (inside or above the basket
    opening), where the red_ball enters first and hits an inner wall.  The gap
    zone covers the majority of seeds confirmed by exhaustive 2-D sweep.

Oracle history:
    Original oracle: ±2.5 x-window → 3-5× too wide, 0/49 impossible seeds found.
    Two-band radial oracle: 38/49 impossible seeds recovered.
    Three-band oracle (this version): adds Band C for basket-tilting mechanism,
    expected to recover the remaining ~10 seeds.
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

    # Geometry for Band C (basket-tilting).
    pg_top = purple_ground.y + purple_ground.thickness / 2
    basket_floor_y = basket.y  # anchor=bottom_center → y is floor bottom

    # Vertical gap between pg surface and basket floor.
    # If the basket starts below pg_top (unusual), the gap is zero and Band C
    # degenerates — attempts will fail is_valid_placement and be skipped.
    gap_y_low = pg_top + radius + 0.01
    gap_y_high = basket_floor_y - 0.01

    # Horizontal range: red_ball can tip the basket from either side.
    x_center = basket.x
    half_span = basket.total_width  # ± one full width from basket center

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
        else:
            # Band C: basket-tilting position — gap zone below basket floor.
            if gap_y_low >= gap_y_high:
                # No usable gap (basket already on ground); fall back to Band A.
                theta = rng.uniform(-math.pi, 0.0)
                d = rng.uniform(sum_r + 0.005, sum_r + 0.10)
                x = float(np.clip(green_ball.x + d * math.cos(theta), -4.5, 4.5))
                y = float(np.clip(green_ball.y + d * math.sin(theta), -4.5, 4.5))
            else:
                x = float(np.clip(
                    rng.uniform(x_center - half_span, x_center + half_span), -4.5, 4.5
                ))
                y = float(rng.uniform(gap_y_low, gap_y_high))

        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("basket_case")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
