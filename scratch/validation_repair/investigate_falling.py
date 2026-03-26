"""Deep investigation into falling_into_place solvability.

For each seed 0-29:
1. Print level geometry parameters
2. Try 1000 random attempts to determine ground-truth solvability
3. For solvable seeds, characterize the valid placement region
"""
import sys

sys.path.insert(0, "/Users/sankaran/Projects/interphyre")

import numpy as np
from interphyre.config import SimulationConfig
from interphyre.levels.falling_into_place import build_level
from interphyre.validation.oracles import _run_attempt

SEEDS = list(range(30))
N_ATTEMPTS = 1000
ORACLE_STEPS = 500
config = SimulationConfig()


def investigate_seed(seed):
    level = build_level(seed=seed)
    gb = level.objects["green_ball"]
    rb = level.objects["red_ball"]
    lb = level.objects["left_bar"]
    rb2 = level.objects["right_bar"]
    bask = level.objects["blue_basket"]
    ramp = level.objects["bottom_ramp"]

    hole_cx = (lb.right + rb2.left) / 2
    hole_width = rb2.left - lb.right
    sum_of_radii = gb.radius + rb.radius
    push_direction = float(np.sign(hole_cx - gb.x))

    params = {
        "bar_y": lb.y,
        "hole_cx": hole_cx,
        "hole_width": hole_width,
        "gb_x": gb.x,
        "gb_y": gb.y,
        "gb_r": gb.radius,
        "rb_r": rb.radius,
        "sum_r": sum_of_radii,
        "push_dir": push_direction,
        "basket_x": bask.x,
        "basket_y": bask.y,
    }

    # Wide random sweep — 1000 attempts
    rng = np.random.default_rng([seed, 0, 1234])
    valid_placements = []
    for _ in range(N_ATTEMPTS):
        x = float(rng.uniform(-4.5, 4.5))
        y = float(rng.uniform(-4.5, 4.5))
        if _run_attempt(level, config, [(x, y, rb.radius)], ORACLE_STEPS):
            valid_placements.append((x, y))

    return params, valid_placements


print(f"{'seed':>4}  {'bar_y':>6}  {'hole_cx':>7}  {'gb_x':>6}  {'gb_y':>6}  "
      f"{'sum_r':>5}  {'push_dir':>8}  {'valid_placements':>30}")
print("-" * 100)

solvable_seeds = []
for s in SEEDS:
    params, placements = investigate_seed(s)
    n = len(placements)
    pstr = str([(f"{x:.2f}", f"{y:.2f}") for x, y in placements[:5]]) if placements else "none"
    if n > 0:
        solvable_seeds.append(s)
    print(
        f"{s:4d}  {params['bar_y']:6.3f}  {params['hole_cx']:7.3f}  "
        f"{params['gb_x']:6.3f}  {params['gb_y']:6.3f}  {params['sum_r']:5.3f}  "
        f"{params['push_dir']:8.1f}  n={n:3d}  {pstr}"
    )

print(f"\nSolvable seeds (1000 attempts): {solvable_seeds}")
print(f"Count: {len(solvable_seeds)}/30")
