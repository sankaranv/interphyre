"""Empirical oracle for catapult.

Two-mechanism design based on catapult arm firing direction:

  UP-RIGHT variant (pivot_x < -3.16): the right arm is heavier; it falls naturally,
  launching green_ball rightward from the left tip. The primary mechanism is an
  explosive overlap — placing the red ball overlapping blue_ball pushes blue_ball
  leftward via Box2D position correction, producing sustained contact with the
  incoming green_ball. Sampling covers the right side of blue_ball (push-left) with
  a near-left extension (to -0.65*br) and a small arm fallback.

  DOWN-LEFT variant (pivot_x >= -3.16): the left arm is heavier; it falls naturally,
  sending green_ball down-left. Placing the red ball on the right arm with low drop
  height counteracts this and launches green_ball into the basket. Concentrated arm
  sampling at just above arm surface (y close to arm_top) and near the right tip is
  far more effective per sample than the wide-range approach.

The -3.16 threshold is derived from the level geometry: arm spans [-4.8, -0.8],
pivot at x = -4.25 + left_side_ratio * 10, threshold where left_side_ratio = 0.109.

Empirically validated against seeds 0-99: 91% valid (9% exhaustion).
True minimum is ~6% (genuinely impossible due to ledge/basket geometry mismatch).
"""
from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_oracle

# pivot_x below this threshold → right arm heavier → UP-RIGHT firing direction
_UP_RIGHT_PIVOT_THRESHOLD = -3.16


@register_oracle("catapult")
def oracle(level, config, n_attempts, oracle_steps, rng):
    pivot_ball = level.objects["pivot_ball"]
    catapult_bar = level.objects["catapult_bar"]
    blue_ball = level.objects["blue_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    arm_right = catapult_bar.x + catapult_bar.length / 2
    arm_top = catapult_bar.y + catapult_bar.thickness / 2
    br = blue_ball.radius

    up_right = pivot_ball.x < _UP_RIGHT_PIVOT_THRESHOLD

    for attempt in range(n_attempts):
        if up_right:
            # Explosive overlap pushes blue_ball toward incoming green_ball.
            if attempt < 35:
                # Right-of-blue_ball: pushes blue leftward to meet green_ball.
                x = np.clip(blue_ball.x + rng.uniform(0.0, br * 0.5), -4.5, 4.5)
                y = np.clip(blue_ball.y + rng.uniform(-br * 0.5, br * 0.5), -4.5, 4.5)
            elif attempt < 43:
                # Left-of-blue_ball extension: seeds where solution is left of center.
                x = np.clip(blue_ball.x - rng.uniform(0.0, br * 0.65), -4.5, 4.5)
                y = np.clip(blue_ball.y + rng.uniform(-br * 0.5, br * 0.5), -4.5, 4.5)
            else:
                # Arm fallback: classic right-arm press.
                x = rng.uniform(np.clip(arm_right - 1.2, -4.5, 4.5), np.clip(arm_right, -4.5, 4.5))
                y = rng.uniform(np.clip(arm_top + 0.02, -4.5, 4.5), np.clip(arm_top + 0.8, -4.5, 4.5))
        else:
            # DOWN-LEFT variant: arm placement near right tip, very low drop height.
            # Concentrated in the empirically effective zone: x near arm_right,
            # y just above arm surface (at+0.005 to at+0.35).
            x = rng.uniform(np.clip(arm_right - 1.0, -4.5, 4.5), np.clip(arm_right, -4.5, 4.5))
            y = rng.uniform(np.clip(arm_top + 0.005, -4.5, 4.5), np.clip(arm_top + 0.35, -4.5, 4.5))

        if _run_attempt(level, config, [(x, y, radius)], oracle_steps):
            return True
    return False
