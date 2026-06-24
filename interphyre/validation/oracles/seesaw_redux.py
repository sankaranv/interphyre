"""Targeted oracle for seesaw_redux (both_barrels).

Two catapults (line_1, line_2) each hold a target ball at one end of a dynamic
pivoting arm.  The solution requires dropping an action ball on the OPPOSITE end
of each arm — this tips the arm and launches the target ball upward.  The two
launched balls then meet somewhere in the air or on the floor.

Key insight: the default action-ball radius (0.5) is too small to reliably hit
the short catapult arm (~2.5 units).  Using larger radii (0.8 – 1.4) gives
sufficient area coverage.  Each action ball should land near the lever end of
its catapult arm — i.e., the end AWAY from the target ball.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("seesaw_redux", max_variants=50, n_attempts=500)


@register_oracle("seesaw_redux")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    line1 = level.objects["line_1"]
    line2 = level.objects["line_2"]

    # Catapult 1 arm tilts at +20°: green ball sits at the LEFT/UPPER end.
    # The lever end (opposite, RIGHT end) is at higher x.
    # Catapult 2 arm tilts at -20°: blue ball sits at the RIGHT/LOWER end.
    # The lever end (LEFT end) is at lower x.
    # line_length = 0.25 * 10 = 2.5; half-length = 1.25
    half_len = 1.25
    arm_angle_deg = 20.0
    cos_a = np.cos(np.radians(arm_angle_deg))
    sin_a = np.sin(np.radians(arm_angle_deg))

    # Lever end of line_1 (right/upper end of the +20° arm):
    lever1_x = line1.x + half_len * cos_a
    lever1_y = line1.y + half_len * sin_a

    # Lever end of line_2 (left/upper end of the -20° arm):
    lever2_x = line2.x - half_len * cos_a
    lever2_y = line2.y + half_len * sin_a  # upper because -20° means left end is higher

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            r = float(rng.uniform(0.8, 1.4))

            if i % 10 < 7:
                # Primary: drop large action balls near the lever ends of each arm.
                dx1 = rng.uniform(-0.8, 0.8)
                dy1 = rng.uniform(0.5, 3.0)
                ax1 = float(np.clip(lever1_x + dx1, -4.5, 4.5))
                ay1 = float(np.clip(lever1_y + dy1, -4.5, 4.5))

                dx2 = rng.uniform(-0.8, 0.8)
                dy2 = rng.uniform(0.5, 3.0)
                ax2 = float(np.clip(lever2_x + dx2, -4.5, 4.5))
                ay2 = float(np.clip(lever2_y + dy2, -4.5, 4.5))
            else:
                # Fallback: random over broader area with the larger radius.
                ax1 = float(rng.uniform(-4.5, 4.5))
                ay1 = float(rng.uniform(-4.5, 4.5))
                ax2 = float(rng.uniform(-4.5, 4.5))
                ay2 = float(rng.uniform(-4.5, 4.5))

            if _run_attempt(env, [(ax1, ay1, r), (ax2, ay2, r)]):
                return True
    finally:
        env.close()
    return False
