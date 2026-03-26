"""Refine the falling_into_place oracle.

Based on v2 investigation: 76/100 seeds solved with reduced push_offset.
Find which seeds are still exhausted and whether they are genuinely
unsolvable or just need a different sampling strategy.

Also tests wider y range (full [-4.5, 4.5]) to see if it helps.
"""
import sys

sys.path.insert(0, "/Users/sankaran/Projects/interphyre")

import numpy as np
from interphyre.config import SimulationConfig
from interphyre.levels.falling_into_place import build_level
from interphyre.validation.oracles import _run_attempt

ORACLE_STEPS = 500
config = SimulationConfig()


def oracle_wide_y(seed, variant=0, n_attempts=50):
    """Reduced push_offset with FULL y range [-4.5, 4.5]."""
    level = build_level(seed=seed, variant=variant)
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius
    sum_of_radii = green_ball.radius + radius

    left_bar = level.objects["left_bar"]
    right_bar = level.objects["right_bar"]
    hole_cx = (left_bar.right + right_bar.left) / 2

    push_direction = float(np.sign(hole_cx - green_ball.x))

    rng = np.random.default_rng([seed, variant, 630])
    for _ in range(n_attempts):
        push_offset = rng.uniform(0.05, sum_of_radii - 0.05)
        x = np.clip(green_ball.x - push_direction * push_offset, -4.5, 4.5)
        # Full y range — include below green ball (may trigger explosive repulsion
        # off the bar that still creates lateral contact).
        y = rng.uniform(-4.5, 4.5)
        if _run_attempt(level, config, [(x, y, radius)], ORACLE_STEPS):
            return True
    return False


def ground_truth_solvable(seed, n_attempts=2000):
    """Wide uniform sweep to determine true solvability."""
    level = build_level(seed=seed)
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius
    rng = np.random.default_rng([seed, 99, 4567])
    for _ in range(n_attempts):
        x = float(rng.uniform(-4.5, 4.5))
        y = float(rng.uniform(-4.5, 4.5))
        if _run_attempt(level, config, [(x, y, radius)], ORACLE_STEPS):
            return True
    return False


# First: test wide_y oracle on seeds 0-99
print("Oracle with full y range [-4.5, 4.5]:")
print("=" * 60)
exhausted_wide = 0
solved_wide = 0
for s in range(100):
    found = False
    for v in range(10):
        if oracle_wide_y(s, v):
            found = True
            break
    if found:
        solved_wide += 1
    else:
        exhausted_wide += 1

print(f"Wide-y oracle — Solved: {solved_wide}/100, Exhausted: {exhausted_wide}/100 ({exhausted_wide}%)")

# Second: for the remaining exhausted seeds, check ground truth solvability
print()
print("Checking ground truth for exhausted seeds (2000 wide attempts each):")
exhausted_seeds = []
for s in range(100):
    found = False
    for v in range(10):
        if oracle_wide_y(s, v):
            found = True
            break
    if not found:
        exhausted_seeds.append(s)

print(f"Exhausted seeds: {exhausted_seeds}")
actually_solvable = []
truly_impossible = []
for s in exhausted_seeds:
    ok = ground_truth_solvable(s, n_attempts=2000)
    if ok:
        actually_solvable.append(s)
        print(f"  seed={s}: SOLVABLE but missed by oracle")
    else:
        truly_impossible.append(s)
        # Print level geometry to understand why
        level = build_level(seed=s)
        gb = level.objects["green_ball"]
        lb = level.objects["left_bar"]
        rb2 = level.objects["right_bar"]
        hole_cx = (lb.right + rb2.left) / 2
        print(
            f"  seed={s}: IMPOSSIBLE — gb_x={gb.x:.3f} gb_y={gb.y:.3f} "
            f"hole_cx={hole_cx:.3f} dist={abs(gb.x - hole_cx):.3f}"
        )

print(f"\nActually solvable but oracle missed: {actually_solvable}")
print(f"Truly impossible seeds: {len(truly_impossible)}")
print(f"True impossibility rate: {len(truly_impossible)}/100 = {len(truly_impossible)}%")
