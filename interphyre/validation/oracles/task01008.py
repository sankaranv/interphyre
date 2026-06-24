"""Targeted oracle for task01008 (Towers).

Mechanism: the task ball (orange goal_block) is embedded in a pyramid of blocks
on a table.  The red ball must strike the pyramid hard enough to dislodge the
goal_block so it falls to the floor.

Strategy: drop the red ball directly above the goal_block.  A small lateral
jitter explores trajectories that topple just the goal block versus the whole
pyramid — either path succeeds if goal_block reaches the floor.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import _run_attempt, register_defaults, register_oracle

register_defaults("task01008", max_variants=20, n_attempts=400)


@register_oracle("task01008")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    goal = level.objects["goal_block"]
    r_red = level.objects["red_ball"].radius

    gx = float(goal.x)
    g_top = float(goal.top)
    half_w = float(goal.width) / 2
    x_min, x_max = -4.5, 4.5

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 8:
                x_offset = rng.uniform(-half_w * 1.5, half_w * 1.5)
                ax = float(np.clip(gx + x_offset, x_min, x_max))
                ay = float(rng.uniform(g_top + r_red, 4.5))
            else:
                ax = float(rng.uniform(x_min, x_max))
                ay = float(rng.uniform(-4.5, 4.5))
            if _run_attempt(env, [(ax, ay, r_red)]):
                return True
    finally:
        env.close()
    return False
