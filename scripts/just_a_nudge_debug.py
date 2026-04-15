"""Debug script: why does the oracle test show 0% on random seeds?

The bundle says 8.3% valid, but testing 100 random seeds [0,9999] shows 0%.
This suggests the oracle n_attempts=50 is too low, or the test seeds were
all impossible by chance. Let's verify by testing known-valid seeds directly.
"""

import json
import lzma
import sys
from pathlib import Path

import numpy as np

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from interphyre.config import SimulationConfig
from interphyre.levels import load_level
from interphyre.validation.oracles import Box2DEngine, _run_attempt
from interphyre.validation.oracles.just_a_nudge import solver as just_a_nudge_solver

_ORACLE_RNG_SALT = 630

bundle_path = repo_root / "interphyre" / "data" / "levels" / "just_a_nudge.json.lzma"
with lzma.open(bundle_path, "rt") as f:
    data = json.load(f)

valid_entries = [e for e in data["entries"] if e["status"] == "valid"]
impossible_entries = [e for e in data["entries"] if e["status"] == "impossible"]

print(f"Bundle: {len(valid_entries)} valid, {len(impossible_entries)} impossible")

config = SimulationConfig()

# ── Test 1: run oracle on first 20 known-valid seeds ──────────────────────────
print("\n--- Testing oracle on 20 known-valid seeds (n_attempts=50) ---")
n_solved = 0
for e in valid_entries[:20]:
    seed = e["seed"]
    variant = e.get("variant", 0)
    level = load_level("just_a_nudge", seed=seed, variant=variant)
    rng = np.random.default_rng([seed, variant, _ORACLE_RNG_SALT])
    result = just_a_nudge_solver(level, config, n_attempts=50, oracle_steps=500, rng=rng)
    status = "SOLVED" if result is not None else "FAILED"
    if result is not None:
        n_solved += 1
    print(f"  seed={seed} variant={variant}: {status}")

print(f"\nOracle solved {n_solved}/20 known-valid seeds")

# ── Test 2: increase n_attempts on known-valid seeds ─────────────────────────
print("\n--- Testing oracle on 20 known-valid seeds (n_attempts=200) ---")
n_solved_200 = 0
for e in valid_entries[:20]:
    seed = e["seed"]
    variant = e.get("variant", 0)
    level = load_level("just_a_nudge", seed=seed, variant=variant)
    rng = np.random.default_rng([seed, variant, _ORACLE_RNG_SALT])
    result = just_a_nudge_solver(level, config, n_attempts=200, oracle_steps=500, rng=rng)
    if result is not None:
        n_solved_200 += 1

print(f"Oracle solved {n_solved_200}/20 known-valid seeds at n_attempts=200")

# ── Test 3: look at what seeds we sampled in the baseline test ────────────────
rng_test = np.random.default_rng(42)
test_seeds_baseline = rng_test.integers(0, 10000, size=100).tolist()

# Are any of them actually valid in the bundle?
valid_seed_set = {e["seed"] for e in valid_entries}
baseline_valid_count = sum(1 for s in test_seeds_baseline if s in valid_seed_set)
print(f"\n--- Baseline test seeds ---")
print(f"100 random seeds: {baseline_valid_count} are known valid in bundle")
print(f"Expected valid: ~{0.083 * 100:.1f}")

# ── Test 4: directly test oracle on valid seeds that appear in our baseline test ──
if baseline_valid_count > 0:
    print("\n--- Testing oracle on baseline seeds that are known valid ---")
    for seed in test_seeds_baseline:
        if seed in valid_seed_set:
            e = next(x for x in valid_entries if x["seed"] == seed)
            variant = e.get("variant", 0)
            level = load_level("just_a_nudge", seed=seed, variant=variant)
            rng = np.random.default_rng([seed, variant, _ORACLE_RNG_SALT])
            result = just_a_nudge_solver(level, config, n_attempts=50, oracle_steps=500, rng=rng)
            print(f"  seed={seed}: {'SOLVED' if result else 'FAILED'}")

# ── Test 5: what platform_angle do invalid seeds in our 100-seed test have? ───
print("\n--- Platform angles of test seeds ---")
from interphyre.objects import Bar, Basket
from interphyre.config import MIN_X, MAX_X, MIN_Y

def get_platform_angle(seed, variant=0):
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))
    _ = rng.uniform(0.2, 0.47)  # green_ball_radius
    _ = rng.uniform(0.8, 1.2)   # basket_scale
    _ = rng.uniform(45, 60)     # ramp_angle
    _ = rng.uniform(0.2, 0.5)   # ball_offset
    _ = rng.uniform(-1.0, 1.0)  # platform_x
    return rng.uniform(-10, 10) # platform_angle

angles = [(s, get_platform_angle(s)) for s in test_seeds_baseline]
pos = [(s, a) for s, a in angles if a >= 0]
neg = [(s, a) for s, a in angles if a < 0]
print(f"Seeds with platform_angle >= 0: {len(pos)}")
print(f"Seeds with platform_angle < 0:  {len(neg)}")

# ── Test 6: test oracle on 50 seeds known to have positive platform_angle ─────
print("\n--- Testing oracle on 50 seeds with platform_angle in [1, 8] (n_attempts=50) ---")
plat_positive_seeds = []
for e in data["entries"]:
    seed = e["seed"]
    variant = e.get("variant", 0)
    angle = get_platform_angle(seed, variant)
    if 1 <= angle <= 8:
        plat_positive_seeds.append((seed, variant))
    if len(plat_positive_seeds) >= 50:
        break

n_solved_plat = 0
for seed, variant in plat_positive_seeds:
    level = load_level("just_a_nudge", seed=seed, variant=variant)
    rng = np.random.default_rng([seed, variant, _ORACLE_RNG_SALT])
    result = just_a_nudge_solver(level, config, n_attempts=50, oracle_steps=500, rng=rng)
    if result is not None:
        n_solved_plat += 1

print(f"Oracle solved {n_solved_plat}/50 seeds with platform_angle in [1, 8]")
print(f"Rate: {n_solved_plat/50:.1%}")
