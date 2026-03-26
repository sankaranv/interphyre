"""Check how many falling_into_place seeds are trivially solved.

The blue_basket is dynamic (falls under gravity). For seeds where the
basket falls and contacts the green_ball naturally, is_trivial should
return True, excluding them from the valid pool.

With the A4 fix (is_trivial checks physics_steps=1000), this matters.
"""
import sys

sys.path.insert(0, "/Users/sankaran/Projects/interphyre")

import numpy as np
from interphyre.levels.falling_into_place import build_level
from interphyre.validation.checks import is_trivial

SEEDS = list(range(100))

trivial_seeds = []
non_trivial_seeds = []

for s in SEEDS:
    level = build_level(seed=s)
    if is_trivial(level, physics_steps=1000):
        trivial_seeds.append(s)
    else:
        non_trivial_seeds.append(s)

print(f"Trivial seeds (out of 100): {len(trivial_seeds)}")
print(f"Non-trivial seeds: {len(non_trivial_seeds)}")
print()
print(f"Trivial seeds: {trivial_seeds}")
