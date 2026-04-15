"""Oracle mechanism audit for a single level — designed to be run in parallel.

Usage:
    python oracle_audit_single.py <level_name>
"""

from __future__ import annotations

import sys
import numpy as np

sys.path.insert(0, "/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre")

from interphyre.levels import load_level
from interphyre.validation.oracles import _run_attempt, Box2DEngine
from interphyre.validation.registry import SeedRegistry
from interphyre.config import SimulationConfig


def grid_sweep(level_name, seed, variant, config, grid_n=12, oracle_steps=400):
    level = load_level(level_name, seed=seed, variant=variant)
    if not level.action_objects:
        return []
    from interphyre.objects import Ball
    action_obj_name = level.action_objects[0]
    action_obj = level.objects[action_obj_name]
    radius = action_obj.radius if isinstance(action_obj, Ball) else 0.3

    engine = Box2DEngine(level=level, config=config)
    found = []
    for x in np.linspace(-4.0, 4.0, grid_n):
        for y in np.linspace(-4.0, 4.0, grid_n):
            if _run_attempt(engine, level, [(float(x), float(y), radius)], oracle_steps=oracle_steps):
                found.append((round(float(x), 2), round(float(y), 2)))
    return found


def main(level_name):
    # Level-specific step overrides for levels with long causal chains
    steps_map = {
        "marble_race": 1500,
        "flagpole_sitta": 1200,
        "keyhole": 600,
    }
    oracle_steps = steps_map.get(level_name, 400)

    config = SimulationConfig()
    reg = SeedRegistry()
    reg._ensure_bundled(level_name)
    bundle = reg._bundled.get(level_name, {})

    impossible_seeds = [
        seed for seed, entry in bundle.items()
        if entry.get("status") == "impossible"
    ]

    if not impossible_seeds:
        print(f"{level_name}: 0 impossible seeds — SKIP")
        return

    n_test = min(5, len(impossible_seeds))
    test_seeds = impossible_seeds[:n_test]
    print(f"\n{level_name}: {len(impossible_seeds)} impossible seeds, testing {n_test}, oracle_steps={oracle_steps}")

    solvable_count = 0
    for seed in test_seeds:
        best_found = []
        best_variant = -1
        for variant in [0, 1, 2]:
            found = grid_sweep(level_name, seed, variant, config,
                               grid_n=12, oracle_steps=oracle_steps)
            if found:
                best_found = found
                best_variant = variant
                break

        if best_found:
            solvable_count += 1
            print(f"  seed={seed} v={best_variant}: SOLVABLE at {best_found[:5]}")
        else:
            print(f"  seed={seed}: NOT solvable (12x12, 3 variants, {oracle_steps} steps)")

    print(f"  SUMMARY: {solvable_count}/{n_test} solvable by grid sweep")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python oracle_audit_single.py <level_name>")
        sys.exit(1)
    main(sys.argv[1])
