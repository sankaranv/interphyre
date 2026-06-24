"""Targeted oracle for task01006 (Unbox).

Mechanism: the container's opening is blocked by a dynamic lid.  The task ball
rolls down the slope but cannot enter until the lid is dislodged.  The red ball
must hit the lid to knock it clear.

Strategy: drop the red ball on or near the lid.  A small lateral jitter finds
the impact position that slides or flips the lid out of the container mouth.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_defaults, register_oracle

register_defaults("task01006", max_variants=20, n_attempts=300)


@register_oracle("task01006")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    lid = level.objects["lid"]
    r_red = level.objects["red_ball"].radius

    lid_cx = float(lid.x)
    lid_top = float(lid.top)
    half_w = float(lid.width) / 2
    x_min, x_max = -4.5, 4.5

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 8:
                x_offset = rng.uniform(-half_w, half_w)
                ax = float(np.clip(lid_cx + x_offset, x_min, x_max))
                ay = float(rng.uniform(lid_top + r_red, 4.5))
            else:
                ax = float(rng.uniform(x_min, x_max))
                ay = float(rng.uniform(-4.5, 4.5))
            if _run_attempt(env, [(ax, ay, r_red)]):
                return True
    finally:
        env.close()
    return False
