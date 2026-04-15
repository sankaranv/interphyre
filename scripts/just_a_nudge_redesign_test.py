"""Redesign empirical tests for just_a_nudge.

Tests redesign options using the oracle on seeds where the parameter constraint
is met, correctly handling variants (the oracle always tests variant=0 first
since the bundle structure just records which variant worked, but the oracle
should test all variants).

KEY INSIGHT from debug: oracle works correctly when called with the right variant.
The "solvability" rate of a redesign must be measured as:
  "fraction of random seeds in [0,9999] that are solvable under the new constraints"
  where solvability is determined by running the oracle on variant 0.
  (The bundle scores variant 0 seeds first, then tries other variants if 0 fails.)

Actually: re-reading the bundle logic, valid entries store the first variant that
works. A seed is "valid" if ANY variant [0..9] solves. For fair redesign testing,
we should test variant=0 only (the canonical player-facing level) since higher
variants change the geometry.

Let's verify: what fraction of valid seeds are solved at variant=0?
"""

import json
import lzma
import sys
from pathlib import Path

import numpy as np

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from interphyre.config import MIN_Y, SimulationConfig
from interphyre.levels import load_level
from interphyre.objects import Bar, Basket
from interphyre.validation.oracles.just_a_nudge import solver as just_a_nudge_solver

_ORACLE_RNG_SALT = 630
config = SimulationConfig()

bundle_path = repo_root / "interphyre" / "data" / "levels" / "just_a_nudge.json.lzma"
with lzma.open(bundle_path, "rt") as f:
    data = json.load(f)

all_entries = data["entries"]
valid_entries = [e for e in all_entries if e["status"] == "valid"]


# ── Helper: extract geometry parameters from seed ────────────────────────────
def extract_geometry(seed, variant=0):
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))
    green_ball_radius = rng.uniform(0.2, 0.47)
    basket_scale = rng.uniform(0.8, 1.2)
    ramp_angle = rng.uniform(45, 60)
    ball_offset = rng.uniform(0.2, 0.5)
    platform_x = rng.uniform(-1.0, 1.0)
    platform_angle = rng.uniform(-10, 10)
    return {
        "ramp_angle": ramp_angle,
        "platform_angle": platform_angle,
        "platform_x": platform_x,
        "green_ball_radius": green_ball_radius,
        "basket_scale": basket_scale,
    }


# ── Confirm: what variant breakdown is in the valid bundle? ──────────────────
variant_counts = {}
for e in valid_entries:
    v = e.get("variant", 0)
    variant_counts[v] = variant_counts.get(v, 0) + 1

print("=== VARIANT BREAKDOWN IN VALID BUNDLE ===")
for v in sorted(variant_counts.keys()):
    pct = 100 * variant_counts[v] / len(valid_entries)
    print(f"  variant {v}: {variant_counts[v]} ({pct:.1f}%)")


# ── Reconfirm platform_angle distribution by variant ─────────────────────────
print("\n=== PLATFORM_ANGLE DISTRIBUTION BY VARIANT ===")
for v in sorted(variant_counts.keys()):
    angles = []
    for e in valid_entries:
        if e.get("variant", 0) == v:
            g = extract_geometry(e["seed"], v)
            angles.append(g["platform_angle"])
    arr = np.array(angles)
    print(f"  variant {v} (n={len(arr)}): mean={arr.mean():.2f}, std={arr.std():.2f}, "
          f"min={arr.min():.2f}, max={arr.max():.2f}")


# ── Now test redesigns properly ───────────────────────────────────────────────
# For each redesign option, we test seeds where:
# 1. The seed's geometry at variant=0 satisfies the new constraint
# 2. We run the oracle on variant=0 only
# This gives us "solvability at variant=0" which approximates the solvability
# rate a player would see (since each seed shows up once, at variant=0).

def oracle_rate_variant0(seeds, label="", n_attempts=50, oracle_steps=500):
    """Test solvability of a batch of seeds at variant=0."""
    n_solved = 0
    n_total = len(seeds)
    for i, seed in enumerate(seeds):
        level = load_level("just_a_nudge", seed=seed, variant=0)
        rng = np.random.default_rng([seed, 0, _ORACLE_RNG_SALT])
        result = just_a_nudge_solver(level, config, n_attempts, oracle_steps, rng)
        if result is not None:
            n_solved += 1
        if (i + 1) % 25 == 0 or i + 1 == n_total:
            print(f"  [{label}] {i+1}/{n_total}: {n_solved}/{i+1} = {n_solved/(i+1):.1%}")
    rate = n_solved / n_total
    print(f"  [{label}] FINAL: {n_solved}/{n_total} = {rate:.1%}")
    return n_solved, n_total, rate


# Baseline: 200 random seeds at variant=0
rng_main = np.random.default_rng(42)
baseline_seeds = rng_main.integers(0, 10000, size=200).tolist()
print("\n=== BASELINE: 200 random seeds, variant=0 ===")
bs_n, bs_t, bs_rate = oracle_rate_variant0(baseline_seeds, label="baseline")


# Redesign test: platform_angle [0, 10] only
# Select seeds (from all_entries) where variant=0 geometry has platform_angle >= 0
seeds_plat_pos = []
for e in all_entries:
    seed = e["seed"]
    g = extract_geometry(seed, variant=0)
    if g["platform_angle"] >= 0:
        seeds_plat_pos.append(seed)
    if len(seeds_plat_pos) >= 5000:
        break

print(f"\n=== REDESIGN A: platform_angle in [0, 10] only ===")
print(f"Seeds with platform_angle >= 0 in first 5000: {len(seeds_plat_pos)}")
print(f"Fraction: {len(seeds_plat_pos)/5000:.1%} (expected ~50%)")
rng_a = np.random.default_rng(100)
test_a = rng_a.choice(seeds_plat_pos[:2000], size=200, replace=False).tolist()
pa_n, pa_t, pa_rate = oracle_rate_variant0(test_a, label="plat>=0")


# Redesign B: platform_angle [1, 8] (positive but not extreme)
seeds_plat_1_8 = []
for e in all_entries:
    seed = e["seed"]
    g = extract_geometry(seed, variant=0)
    if 1 <= g["platform_angle"] <= 8:
        seeds_plat_1_8.append(seed)
    if len(seeds_plat_1_8) >= 4000:
        break

print(f"\n=== REDESIGN B: platform_angle in [1, 8] ===")
print(f"Seeds in range: {len(seeds_plat_1_8)}")
rng_b = np.random.default_rng(200)
test_b = rng_b.choice(seeds_plat_1_8[:1500], size=200, replace=False).tolist()
pb_n, pb_t, pb_rate = oracle_rate_variant0(test_b, label="plat[1,8]")


# Redesign C: platform_angle [0, 6] (main sweet spot from distribution analysis)
seeds_plat_0_6 = []
for e in all_entries:
    seed = e["seed"]
    g = extract_geometry(seed, variant=0)
    if 0 <= g["platform_angle"] <= 6:
        seeds_plat_0_6.append(seed)
    if len(seeds_plat_0_6) >= 4000:
        break

print(f"\n=== REDESIGN C: platform_angle in [0, 6] ===")
print(f"Seeds in range: {len(seeds_plat_0_6)}")
rng_c = np.random.default_rng(300)
test_c = rng_c.choice(seeds_plat_0_6[:1500], size=200, replace=False).tolist()
pc_n, pc_t, pc_rate = oracle_rate_variant0(test_c, label="plat[0,6]")


# ── Summary ───────────────────────────────────────────────────────────────────
print("\n\n=== FINAL SUMMARY ===")
print(f"Baseline (current level, all platform_angles):  {bs_rate:.1%}")
print(f"Redesign A (platform_angle >= 0):               {pa_rate:.1%}")
print(f"Redesign B (platform_angle in [1, 8]):          {pb_rate:.1%}")
print(f"Redesign C (platform_angle in [0, 6]):          {pc_rate:.1%}")
print()
print("Note: These rates measure variant=0 solvability (what a player sees).")
print("The bundle rate (8.3%) counts seeds solvable at ANY variant [0..9].")
print()

# Compute expected improvement from restricting platform_angle
# The distribution analysis showed ~88-92% solvability for plat in [0,6]
# But only ~20% of seeds have plat >= 0 at variant=0.
# Under the new constraint, ALL seeds would have plat >= 0.
# So projected rate = rate_at_plat_positive * 1.0 = pa_rate
print(f"Expected solvability if platform_angle restricted to [0, 6]: ~{pc_rate:.0%}")
print(f"This {'meets' if pc_rate >= 0.50 else 'does NOT meet'} the 50% target.")
