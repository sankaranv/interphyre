"""Empirical test script for falling_into_place oracle redesign.

Tests two placement strategies across seeds 0-29 to identify what
actually achieves success:

A) Reduced push_offset: push_offset in [0.05, sum_of_radii - 0.05]
   — red ball falls beside and contacts green ball laterally
B) Wide sweep: sample entire world region to find any valid placements

Reports success rate and characterizes valid placement regions.
"""
import sys

sys.path.insert(0, "/Users/sankaran/Projects/interphyre")

import numpy as np
from interphyre.config import SimulationConfig
from interphyre.levels.falling_into_place import build_level
from interphyre.validation.oracles import _run_attempt

SEEDS = list(range(30))
N_WIDE = 200  # wide sweep attempts per seed
N_VARIANTS = 3
ORACLE_STEPS = 500
config = SimulationConfig()


def test_reduced_push_offset(seed):
    """Try placing red ball on far side with push_offset < sum_of_radii."""
    level = build_level(seed=seed)
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius
    sum_of_radii = green_ball.radius + radius

    left_bar = level.objects["left_bar"]
    right_bar = level.objects["right_bar"]
    hole_cx = (left_bar.right + right_bar.left) / 2

    push_direction = float(np.sign(hole_cx - green_ball.x))

    rng = np.random.default_rng([seed, 0, 9999])
    for _ in range(100):
        # Reduced push_offset: in [0.05, sum_of_radii - 0.05]
        # So falling ball CAN contact green ball at height green_ball.y
        push_offset = rng.uniform(0.05, sum_of_radii - 0.05)
        x = np.clip(green_ball.x - push_direction * push_offset, -4.5, 4.5)
        y_base = green_ball.y + sum_of_radii + 0.05
        y = rng.uniform(np.clip(y_base, -4.5, 4.5), np.clip(y_base + 2.0, -4.5, 4.5))
        if _run_attempt(level, config, [(x, y, radius)], ORACLE_STEPS):
            return True, x, y, push_offset
    return False, None, None, None


def test_wide_sweep(seed):
    """Uniform random placement over [-4.5, 4.5]^2 to find any valid placement."""
    level = build_level(seed=seed)
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    rng = np.random.default_rng([seed, 0, 7777])
    for _ in range(N_WIDE):
        x = float(rng.uniform(-4.5, 4.5))
        y = float(rng.uniform(-4.5, 4.5))
        if _run_attempt(level, config, [(x, y, radius)], ORACLE_STEPS):
            return True, x, y
    return False, None, None


def test_direct_above(seed):
    """Drop directly above the green ball."""
    level = build_level(seed=seed)
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius
    sum_of_radii = green_ball.radius + radius

    rng = np.random.default_rng([seed, 0, 8888])
    for _ in range(50):
        x = float(green_ball.x + rng.uniform(-0.1, 0.1))
        y_base = green_ball.y + sum_of_radii + 0.05
        y = rng.uniform(np.clip(y_base, -4.5, 4.5), np.clip(y_base + 2.0, -4.5, 4.5))
        if _run_attempt(level, config, [(x, y, radius)], ORACLE_STEPS):
            return True, x, y
    return False, None, None


print("=" * 60)
print("Strategy A: Reduced push_offset [0.05, sum_of_radii - 0.05]")
print("=" * 60)
a_successes = 0
for s in SEEDS:
    ok, x, y, po = test_reduced_push_offset(s)
    if ok:
        a_successes += 1
        gbx = build_level(seed=s).objects["green_ball"].x
        hole_cx = (
            build_level(seed=s).objects["left_bar"].right
            + build_level(seed=s).objects["right_bar"].left
        ) / 2
        print(
            f"  seed={s:3d}: VALID  x={x:.3f} y={y:.3f} push_offset={po:.3f}  "
            f"(gb.x={gbx:.3f}, hole_cx={hole_cx:.3f})"
        )
    else:
        print(f"  seed={s:3d}: miss")

print(f"\nStrategy A success rate: {a_successes}/{len(SEEDS)}")

print()
print("=" * 60)
print("Strategy B: Direct drop above green ball")
print("=" * 60)
b_successes = 0
for s in SEEDS:
    ok, x, y = test_direct_above(s)
    if ok:
        b_successes += 1
        print(f"  seed={s:3d}: VALID  x={x:.3f} y={y:.3f}")
    else:
        print(f"  seed={s:3d}: miss")

print(f"\nStrategy B success rate: {b_successes}/{len(SEEDS)}")

print()
print("=" * 60)
print("Wide sweep (ground truth solvability)")
print("=" * 60)
wide_successes = 0
for s in SEEDS:
    ok, x, y = test_wide_sweep(s)
    if ok:
        wide_successes += 1
        print(f"  seed={s:3d}: SOLVABLE  x={x:.3f} y={y:.3f}")
    else:
        print(f"  seed={s:3d}: missed in {N_WIDE} attempts")

print(f"\nWide sweep solvable: {wide_successes}/{len(SEEDS)}")
