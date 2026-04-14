"""Sample 20 impossible catapult seeds and run 15x15 full-board grid sweep.

Distinguishes oracle false negatives (FNR) from genuine geometric impossibility.
A 15x15 grid × 4 radii = 900 attempts per seed at oracle_steps=1000.
"""
import lzma
import json
import sys
import numpy as np

sys.path.insert(0, '/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre')
from interphyre.validation.oracles import Box2DEngine
from interphyre.validation.placement import is_valid_placement
from interphyre.levels import load_level
from interphyre.config import SimulationConfig


def grid_sweep(level, config, grid_n=15, oracle_steps=1000):
    """15x15 full-board grid sweep across 4 radii. Returns (found, x, y, r)."""
    for r in [0.9, 1.0, 1.1, 1.2]:
        xs = np.linspace(-4.2, 4.2, grid_n)
        ys = np.linspace(-4.2, 4.2, grid_n)
        for x in xs:
            for y in ys:
                if not is_valid_placement(level, float(x), float(y), r):
                    continue
                engine = Box2DEngine(level=level, config=config)
                engine.place_action_objects([(float(x), float(y), r)])
                success = False
                for _ in range(oracle_steps):
                    engine.world.Step(
                        config.time_step, config.velocity_iters, config.position_iters
                    )
                    engine.time_update(config.time_step)
                    if level.success_condition(engine):
                        success = True
                        break
                if success:
                    return (True, float(x), float(y), r)
    return (False, None, None, None)


def main():
    bundle_path = (
        '/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre'
        '/interphyre/data/levels/catapult.json.lzma'
    )
    with lzma.open(bundle_path) as f:
        data = json.load(f)

    entries = data['entries']
    impossible_seeds = sorted({e['seed'] for e in entries if e['status'] == 'impossible'})
    print(f"Total impossible seeds: {len(impossible_seeds)}", flush=True)

    rng = np.random.default_rng(42)
    sample = sorted(rng.choice(impossible_seeds, size=min(20, len(impossible_seeds)), replace=False).tolist())
    print(f"Sampling {len(sample)} seeds: {sample}", flush=True)
    print("", flush=True)

    config = SimulationConfig()
    found_count = 0

    for seed in sample:
        level = load_level('catapult', seed=seed, variant=0)
        found, x, y, r = grid_sweep(level, config, grid_n=15, oracle_steps=1000)
        if found:
            found_count += 1
            print(f"  seed={seed}: FOUND at ({x:.2f}, {y:.2f}) r={r:.2f}", flush=True)
        else:
            print(f"  seed={seed}: IMPOSSIBLE (grid exhausted)", flush=True)

    print("", flush=True)
    print(f"Summary: {found_count}/{len(sample)} seeds are oracle false negatives", flush=True)
    print(f"Estimated FNR: {100.0 * found_count / len(sample):.1f}%", flush=True)
    est_true_impossible = (1 - found_count / len(sample)) * len(impossible_seeds)
    print(
        f"Estimated true impossible seeds: ~{est_true_impossible:.0f} "
        f"({100.0 * est_true_impossible / 10001:.1f}% of all seeds)",
        flush=True,
    )

    # Also print Zone A stats for impossible seeds to look for parameter patterns
    print("\nLevel parameter analysis for a few impossible seeds:", flush=True)
    for seed in sample[:5]:
        level = load_level('catapult', seed=seed, variant=0)
        gp = level.objects['gray_platform']
        arm_right = gp.x + gp.length / 2
        arm_top = gp.y + gp.thickness / 2
        print(f"  seed={seed}: arm_right={arm_right:.2f}, arm_top={arm_top:.2f}, "
              f"platform.x={gp.x:.2f}, platform.length={gp.length:.2f}", flush=True)


if __name__ == '__main__':
    main()
