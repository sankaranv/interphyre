"""Test the improved oracle for falling_into_place.

Empirical finding: valid placements require push_offset < sum_of_radii
(so the falling red ball can make lateral contact with the green ball).
The current spec oracle uses push_offset > sum_of_radii → never contacts.

Tests two oracle strategies on seeds 0-99:
  A) Reduced push_offset: uniform(0.05, sum_of_radii - 0.05)
     — falling ball contacts green ball laterally
  B) Two-region: A + near-hole sampling for push_dir=+1 seeds
"""
import sys

sys.path.insert(0, "/Users/sankaran/Projects/interphyre")

import numpy as np
from interphyre.config import SimulationConfig
from interphyre.levels.falling_into_place import build_level
from interphyre.validation.oracles import _run_attempt

SEEDS = list(range(100))
N_ATTEMPTS = 50
ORACLE_STEPS = 500
config = SimulationConfig()


def oracle_v2(seed, variant=0):
    """Reduced push_offset oracle: push from far side with contact-range offset."""
    level = build_level(seed=seed, variant=variant)
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius
    sum_of_radii = green_ball.radius + radius

    left_bar = level.objects["left_bar"]
    right_bar = level.objects["right_bar"]
    hole_cx = (left_bar.right + right_bar.left) / 2

    push_direction = float(np.sign(hole_cx - green_ball.x))

    rng = np.random.default_rng([seed, variant, 630])  # same salt as validation module
    for i in range(N_ATTEMPTS):
        # Reduced push_offset: in [0.05, sum_of_radii - 0.05]
        # This ensures the falling red ball contacts the green ball laterally.
        push_offset = rng.uniform(0.05, sum_of_radii - 0.05)
        x = np.clip(green_ball.x - push_direction * push_offset, -4.5, 4.5)
        # Drop from above: start at sum_of_radii above green ball (no initial overlap).
        y_base = green_ball.y + sum_of_radii + 0.05
        y = rng.uniform(np.clip(y_base, -4.5, 4.5), 4.5)
        if _run_attempt(level, config, [(x, y, radius)], ORACLE_STEPS):
            return True
    return False


def oracle_v3(seed, variant=0):
    """Two-region oracle: lateral push + near-hole fallback.

    Region 0 (every other attempt): reduced push_offset lateral contact.
    Region 1 (alternating): near-hole sampling (for push_dir=+1 seeds where
    the ball on the LEFT needs a different causal path).
    """
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
    for i in range(N_ATTEMPTS):
        if i % 2 == 0:
            # Region 0: lateral contact push from opposite side
            push_offset = rng.uniform(0.05, sum_of_radii - 0.05)
            x = np.clip(green_ball.x - push_direction * push_offset, -4.5, 4.5)
            y_base = green_ball.y + sum_of_radii + 0.05
            y = rng.uniform(np.clip(y_base, -4.5, 4.5), 4.5)
        else:
            # Region 1: near the hole (wider lateral range + higher drop)
            # Concentrates on the area just beyond the green ball toward hole_cx.
            # For push_dir=+1 seeds, green ball is left and hole is right — sampling
            # near the far right edge of the hole can find indirect path solutions.
            x = rng.uniform(
                np.clip(hole_cx - 1.0, -4.5, 4.5),
                np.clip(hole_cx + 1.0, -4.5, 4.5),
            )
            y = rng.uniform(
                np.clip(green_ball.y - 0.5, -4.5, 4.5),
                np.clip(green_ball.y + 2.5, -4.5, 4.5),
            )
        if _run_attempt(level, config, [(x, y, radius)], ORACLE_STEPS):
            return True
    return False


# Test oracle v2 on seeds 0-99 with max_variants=10
print("Testing oracle_v2 (reduced push_offset, 50 attempts, max 10 variants)")
print("=" * 60)

exhausted_v2 = 0
solved_v2 = 0
for s in SEEDS:
    found = False
    for v in range(10):
        if oracle_v2(s, v):
            found = True
            break
    if found:
        solved_v2 += 1
    else:
        exhausted_v2 += 1

print(f"V2 — Solved: {solved_v2}/100, Exhausted: {exhausted_v2}/100 ({exhausted_v2}%)")
print()

# Test oracle v3 on seeds 0-99 with max_variants=10
print("Testing oracle_v3 (two-region, 50 attempts, max 10 variants)")
print("=" * 60)

exhausted_v3 = 0
solved_v3 = 0
for s in SEEDS:
    found = False
    for v in range(10):
        if oracle_v3(s, v):
            found = True
            break
    if found:
        solved_v3 += 1
    else:
        exhausted_v3 += 1

print(f"V3 — Solved: {solved_v3}/100, Exhausted: {exhausted_v3}/100 ({exhausted_v3}%)")
