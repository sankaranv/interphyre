"""Test 3-region oracle for falling_into_place.

Region 0+1 (2/3 of attempts): lateral contact push (reduced push_offset)
Region 2 (1/3 of attempts): drop near hole edge (indirect causal path for
seeds where green ball is far from hole but some path via the hole works)
"""
import sys

sys.path.insert(0, "/Users/sankaran/Projects/interphyre")

import numpy as np
from interphyre.config import SimulationConfig
from interphyre.levels.falling_into_place import build_level
from interphyre.validation.oracles import _run_attempt

ORACLE_STEPS = 500
config = SimulationConfig()


def oracle_v4(seed, variant=0, n_attempts=50):
    """Three-region oracle."""
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
    for i in range(n_attempts):
        region = i % 3

        if region < 2:
            # Lateral contact push: push_offset < sum_of_radii so falling ball
            # contacts green ball and delivers a lateral impulse toward the hole.
            push_offset = rng.uniform(0.05, sum_of_radii - 0.05)
            x = np.clip(green_ball.x - push_direction * push_offset, -4.5, 4.5)
            y = rng.uniform(-4.5, 4.5)
        else:
            # Near-hole-edge drop: red ball falls through or near the far edge
            # of the hole. For some seeds this creates an indirect causal chain
            # via the bottom ramp and the dynamic basket.
            if push_direction > 0:
                # Hole is to the right: drop near right edge of hole
                x = rng.uniform(
                    np.clip(right_bar.left - 0.3, -4.5, 4.5),
                    np.clip(right_bar.left + 0.1, -4.5, 4.5),
                )
            else:
                # Hole is to the left: drop near left edge of hole
                x = rng.uniform(
                    np.clip(left_bar.right - 0.1, -4.5, 4.5),
                    np.clip(left_bar.right + 0.3, -4.5, 4.5),
                )
            y = rng.uniform(
                np.clip(green_ball.y - 0.5, -4.5, 4.5),
                np.clip(green_ball.y + 2.5, -4.5, 4.5),
            )

        if _run_attempt(level, config, [(x, y, radius)], ORACLE_STEPS):
            return True
    return False


# Test over seeds 0-99, max 10 variants
print("Testing oracle_v4 (3-region: lateral push + near-hole fallback)")
print("=" * 60)

exhausted = 0
solved = 0
exhausted_seeds = []
for s in range(100):
    found = False
    for v in range(10):
        if oracle_v4(s, v):
            found = True
            break
    if found:
        solved += 1
    else:
        exhausted += 1
        exhausted_seeds.append(s)

print(f"Solved: {solved}/100, Exhausted: {exhausted}/100 ({exhausted}%)")
print(f"Exhausted seeds: {exhausted_seeds}")
