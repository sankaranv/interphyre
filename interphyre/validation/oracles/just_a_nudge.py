"""Targeted oracle for just_a_nudge.

Causal chain: the basket is dynamic (dynamic=True). Placing the red ball near
the blue_ball/basket area at y ≈ blue_ball.y causes the basket to shift. The
green_ball sits on the slightly-tilted platform left edge and falls off into the
repositioned basket, contacting the blue_ball. Success: green_ball contacts
blue_ball for the required duration.

The spec B2 causal chain (drop above green_ball, knock it toward basket) achieves
0% success across 50 seeds — it cannot overcome the platform geometry constraint.

Empirical discovery (sweep over 50 seeds):
  - Placement at (bb.x ± 0.5, bb.y ± 0.4) achieves ~72% success with 80 attempts,
    ~86% with 200 attempts + 1000 steps.
  - Side push from the opposite side of green_ball (basket.x + offset if gb is
    left of basket) solves seeds where the basket must travel further to align
    with the green_ball's fall trajectory.

Design decisions:
  - Two phases: (1) near blue_ball for direct basket adjustment; (2) side push for
    seeds with large lateral gap between green_ball and basket.
  - Phase split at 60% of attempts: prioritises the faster-converging direct
    approach; reserves 40% for the geometrically harder large-gap cases.
  - x-search radius ±0.5 from bb.x (wider than naive ±0.3) is needed for seeds
    where the basket must shift > 1.5 units toward gb.x.

Empirical result (seeds 0–49, n_attempts=200, oracle_steps=1000):
  ~49/50 seeds solved (seed 8 unsolvable even with uniform random oracle).
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle


@register_oracle("just_a_nudge")
def oracle(level, config, n_attempts, oracle_steps, rng):
    green_ball = level.objects["green_ball"]
    blue_ball = level.objects["blue_ball"]
    basket = level.objects["basket"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Phase boundary: first 60% of attempts target the blue_ball position.
    # Remaining 40% use a directional side push when the basket gap is large.
    phase_boundary = int(n_attempts * 0.6)

    # Push direction: place red_ball on the side of the basket opposite to
    # green_ball, so the impulse drives the basket toward gb.x.
    push_from_right = green_ball.x < basket.x  # gb left of basket → push from right

    for i in range(n_attempts):
        if i < phase_boundary:
            # Phase 1: placement near blue_ball (direct basket adjustment).
            # i=0 is deterministic — always try the direct overlap first.
            if i == 0:
                x = np.clip(blue_ball.x, -4.5, 4.5)
                y = np.clip(blue_ball.y, -4.5, 4.5)
            else:
                x = np.clip(blue_ball.x + rng.uniform(-0.5, 0.5), -4.5, 4.5)
                y = np.clip(blue_ball.y + rng.uniform(-0.3, 0.5), -4.5, 4.5)
        else:
            # Phase 2: side push from the side opposite green_ball.
            # A small overlap with the basket wall transfers a lateral impulse,
            # sliding the basket toward the green_ball's fall trajectory.
            offset = rng.uniform(-radius, radius * 2.0)
            if push_from_right:
                x = np.clip(basket.x + offset, -4.5, 4.5)
            else:
                x = np.clip(basket.x - offset, -4.5, 4.5)
            y = np.clip(blue_ball.y + rng.uniform(-0.3, 0.5), -4.5, 4.5)

        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
