"""Investigate valid placements for the 7 seeds that are solvable but missed by oracle.

Seeds: 8, 14, 24, 38, 48, 66, 67
For each: run 5000 random wide-sweep attempts, collect valid placements,
and characterize the pattern to inform oracle design.
"""
import sys

sys.path.insert(0, "/Users/sankaran/Projects/interphyre")

import numpy as np
from interphyre.config import SimulationConfig
from interphyre.levels.falling_into_place import build_level
from interphyre.validation.oracles import _run_attempt

MISSED_SEEDS = [8, 14, 24, 38, 48, 66, 67]
N_ATTEMPTS = 5000
ORACLE_STEPS = 500
config = SimulationConfig()


for s in MISSED_SEEDS:
    level = build_level(seed=s)
    gb = level.objects["green_ball"]
    rb = level.objects["red_ball"]
    lb = level.objects["left_bar"]
    rb2 = level.objects["right_bar"]

    hole_cx = (lb.right + rb2.left) / 2
    sum_r = gb.radius + rb.radius
    push_dir = float(np.sign(hole_cx - gb.x))

    print(f"\nseed={s}: gb_x={gb.x:.3f} gb_y={gb.y:.3f} hole_cx={hole_cx:.3f} "
          f"sum_r={sum_r:.3f} push_dir={push_dir:.0f} bar_y={lb.y:.3f}")

    rng = np.random.default_rng([s, 0, 9876])
    valid = []
    for _ in range(N_ATTEMPTS):
        x = float(rng.uniform(-4.5, 4.5))
        y = float(rng.uniform(-4.5, 4.5))
        if _run_attempt(level, config, [(x, y, rb.radius)], ORACLE_STEPS):
            valid.append((x, y))

    if valid:
        xs = [v[0] for v in valid]
        ys = [v[1] for v in valid]
        print(f"  Found {len(valid)}/{N_ATTEMPTS} valid placements ({100*len(valid)/N_ATTEMPTS:.1f}%)")
        print(f"  x range: [{min(xs):.3f}, {max(xs):.3f}]  (gb.x={gb.x:.3f})")
        print(f"  y range: [{min(ys):.3f}, {max(ys):.3f}]  (gb.y={gb.y:.3f})")
        print(f"  First 10 valid placements (x, y):")
        for v in valid[:10]:
            dx = v[0] - gb.x
            dy = v[1] - gb.y
            print(f"    x={v[0]:.3f} y={v[1]:.3f}  (dx={dx:+.3f} dy={dy:+.3f})")
    else:
        print(f"  NO valid placements found in {N_ATTEMPTS} attempts!")
