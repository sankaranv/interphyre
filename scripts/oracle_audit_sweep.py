"""Oracle mechanism audit: grid sweep for impossible seeds.

For each level with impossible seeds, pick up to 5 impossible seeds (variant=0),
run a 15x15 grid sweep across the full board to determine whether any placement
solves the level regardless of where the oracle samples.

Reports: for each (seed, variant), whether solutions exist outside oracle zones.
"""

from __future__ import annotations

import sys
import numpy as np

sys.path.insert(0, "/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre")

from interphyre.levels import load_level
from interphyre.validation.oracles import _run_attempt, Box2DEngine
from interphyre.validation.registry import SeedRegistry
from interphyre.config import SimulationConfig


def grid_sweep(level_name: str, seed: int, variant: int, config: SimulationConfig,
               grid_n: int = 15, oracle_steps: int = 300) -> list[tuple[float, float]]:
    """Run a grid_n x grid_n sweep and return winning positions."""
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
                found.append((float(x), float(y)))
    return found


def main():
    config = SimulationConfig()
    reg = SeedRegistry()

    # Levels with impossible seeds (non-100% valid rate or known impossible stragglers)
    levels_to_audit = [
        ("catapult",           1332, 300),   # 25.8%
        ("just_a_nudge",       9169, 300),   # 8.3%
        ("locust_swarm",       2543, 300),   # 74.6%
        ("the_cradle",         2143, 300),   # 78.6%
        ("pinball_machine",    1286, 300),   # 87.1%
        ("staircase",           303, 300),   # 97.0%
        ("the_funnel",          122, 300),   # 98.8%
        ("keyhole",              86, 400),   # 99.1% — needs more steps for causal chain
        ("mind_the_gap",         62, 300),   # 99.4%
        ("dive_bomb",            64, 300),   # 99.4%
        ("falling_into_place",   21, 300),   # 99.8%
        ("pass_the_parcel",      18, 300),   # 99.8%
        ("straight_face",         6, 300),   # 99.9%
        ("off_the_rails",         3, 300),   # ~100% but 3 impossible
        ("zebra_crossing",        5, 300),   # 100% (5 known stragglers per docstring)
    ]

    for level_name, n_impossible, oracle_steps in levels_to_audit:
        reg._ensure_bundled(level_name)
        bundle = reg._bundled.get(level_name, {})

        impossible_seeds = [
            seed
            for seed, entry in bundle.items()
            if entry.get("status") == "impossible"
        ]

        if not impossible_seeds:
            print(f"=== {level_name}: 0 impossible seeds in bundle — SKIP ===", flush=True)
            continue

        n_test = min(5, len(impossible_seeds))
        test_seeds = impossible_seeds[:n_test]
        print(f"\n=== {level_name}: {len(impossible_seeds)} impossible seeds, testing {n_test} ===", flush=True)

        solvable_count = 0
        for seed in test_seeds:
            # Try variant=0 first, then variant=1, variant=2 if 0 yields nothing
            best_found = []
            best_variant = -1
            for variant in [0, 1, 2]:
                found = grid_sweep(level_name, seed, variant, config, grid_n=15, oracle_steps=oracle_steps)
                if found:
                    best_found = found
                    best_variant = variant
                    break

            if best_found:
                solvable_count += 1
                print(f"  seed={seed} variant={best_variant}: SOLVABLE at {best_found[:3]}", flush=True)
            else:
                print(f"  seed={seed}: NOT solvable (15x15 grid, variants 0-2, steps={oracle_steps})", flush=True)

        print(f"  SUMMARY: {solvable_count}/{n_test} impossible seeds solvable by grid sweep", flush=True)


if __name__ == "__main__":
    main()
