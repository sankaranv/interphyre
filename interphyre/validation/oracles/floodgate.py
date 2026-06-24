"""Targeted oracle for floodgate.

Mechanism: a lid covers the gap between the slope and the open container.  The
task ball rolls down the slope but cannot reach the container while the lid
blocks the entry.  The red ball must knock the lid aside to open the gap.

Strategy: drop the red ball directly on the lid.  A lateral x-jitter explores
the range of impact angles that will slide or topple the lid clear of the gap.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_defaults, register_oracle

register_defaults("floodgate", max_variants=20, n_attempts=300)


@register_oracle("floodgate")
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
