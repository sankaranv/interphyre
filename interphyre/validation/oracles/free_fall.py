"""Targeted oracle for free_fall.

Mechanism: the dynamic bracket (container) holds the task ball in mid-air.
The bracket falls under gravity, but because it is open at the top, the ball
only touches the world floor if the bracket tips and spills it out.  The red
ball is aimed at the rim of the bracket to tip it on landing.

Strategy: drop near the container x with a lateral offset toward the rim, so
the bracket tilts and the ball exits through the open top as the container hits
the floor.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_defaults, register_oracle

register_defaults("free_fall", max_variants=20, n_attempts=300)


@register_oracle("free_fall")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    container = level.objects["container"]
    r_red = level.objects["red_ball"].radius

    cx = float(container.x)
    # Top of the container opening (bracket is open at the top).
    c_top = float(container.y) + float(container.height)
    half_w = float(container.width) / 2
    x_min, x_max = -4.5, 4.5

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 8:
                # Aim near the rim on either side to tip the container.
                side = 1.0 if rng.integers(0, 2) == 0 else -1.0
                x_offset = rng.uniform(half_w * 0.3, half_w + r_red)
                ax = float(np.clip(cx + side * x_offset, x_min, x_max))
                ay = float(rng.uniform(c_top + r_red, 4.5))
            else:
                ax = float(rng.uniform(x_min, x_max))
                ay = float(rng.uniform(-4.5, 4.5))
            if _run_attempt(env, [(ax, ay, r_red)]):
                return True
    finally:
        env.close()
    return False
