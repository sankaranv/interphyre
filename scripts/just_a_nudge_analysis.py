"""Analysis script for just_a_nudge redesign.

Reads the bundle, reconstructs level geometry for valid and impossible seeds,
measures the joint distribution of (ramp_angle, platform_angle), identifies
the root cause of impossibility, and empirically tests redesign options.
"""

import json
import lzma
import sys
from pathlib import Path

import numpy as np

# Add repo root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from interphyre.config import MIN_X, MAX_X, MIN_Y, SimulationConfig
from interphyre.levels import load_level
from interphyre.objects import Bar, Basket
from interphyre.validation.oracles import get_oracle, Box2DEngine, _run_attempt

# ── Load bundle ────────────────────────────────────────────────────────────────
bundle_path = repo_root / "interphyre" / "data" / "levels" / "just_a_nudge.json.lzma"
with lzma.open(bundle_path, "rt") as f:
    data = json.load(f)

all_entries = data["entries"]
valid_entries = [e for e in all_entries if e["status"] == "valid"]
impossible_entries = [e for e in all_entries if e["status"] == "impossible"]

print(f"Total entries: {len(all_entries)}")
print(f"Valid: {len(valid_entries)} ({100*len(valid_entries)/len(all_entries):.1f}%)")
print(f"Impossible: {len(impossible_entries)} ({100*len(impossible_entries)/len(all_entries):.1f}%)")


# ── Extract geometry from a seed using the deterministic RNG ──────────────────
def extract_geometry(seed, variant=0):
    """Reconstruct the level geometry parameters from seed via the same RNG sequence."""
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    green_ball_radius = rng.uniform(0.2, 0.47)
    basket_scale = rng.uniform(0.8, 1.2)
    ramp_angle = rng.uniform(45, 60)
    ball_offset = rng.uniform(0.2, 0.5)
    platform_x = rng.uniform(-1.0, 1.0)
    platform_angle = rng.uniform(-10, 10)

    # Derived quantities
    ramp_height = 2.0
    floor_distance = ramp_height / np.tan(np.radians(ramp_angle))

    basket_dims = Basket.calculate_dimensions(basket_scale)
    basket_top = (MIN_Y + 0.1) + basket_dims["total_height"]

    min_platform_bottom = max(-2.0, basket_top + green_ball_radius * 4)
    platform_length = 3.5
    platform_center_y = min_platform_bottom + platform_length / 2

    # Build the platform Bar to get .left and .right
    platform = Bar.from_point_and_angle(
        x=platform_x,
        y=platform_center_y,
        angle=platform_angle,
        length=platform_length,
        thickness=0.2,
        color="black",
        dynamic=False,
    )

    max_basket_x = platform.right + 0.39 - basket_dims["total_width"] / 2
    basket_x = rng.uniform(-1.0, min(1.0, max_basket_x))

    green_ball_x = platform.left + ball_offset + green_ball_radius
    platform_top_surface = platform_center_y + platform_length / 2
    green_ball_y = platform_top_surface + green_ball_radius

    return {
        "seed": seed,
        "variant": variant,
        "ramp_angle": ramp_angle,
        "platform_angle": platform_angle,
        "platform_x": platform_x,
        "basket_scale": basket_scale,
        "green_ball_radius": green_ball_radius,
        "ball_offset": ball_offset,
        "green_ball_x": green_ball_x,
        "green_ball_y": green_ball_y,
        "basket_x": basket_x,
        "floor_distance": floor_distance,
        "platform_left": platform.left,
        "platform_right": platform.right,
        "platform_center_y": platform_center_y,
        "dx_basket_green": basket_x - green_ball_x,
    }


# ── Extract geometry for all valid seeds ─────────────────────────────────────
print("\n--- Extracting geometry for all valid seeds ---")
valid_geoms = []
for e in valid_entries:
    g = extract_geometry(e["seed"], e.get("variant", 0))
    valid_geoms.append(g)

# ── Sample 300 impossible seeds for comparison ────────────────────────────────
print("--- Extracting geometry for 300 sampled impossible seeds ---")
rng_sample = np.random.default_rng(9999)
impossible_sample = rng_sample.choice(impossible_entries, size=min(300, len(impossible_entries)), replace=False)
impossible_geoms = []
for e in impossible_sample:
    g = extract_geometry(e["seed"], e.get("variant", 0))
    impossible_geoms.append(g)


def stats(arr, label):
    arr = np.array(arr)
    print(f"  {label}: mean={arr.mean():.3f}, std={arr.std():.3f}, "
          f"min={arr.min():.3f}, p25={np.percentile(arr, 25):.3f}, "
          f"p50={np.percentile(arr, 50):.3f}, p75={np.percentile(arr, 75):.3f}, "
          f"max={arr.max():.3f}")
    return arr


# ── Distribution analysis ─────────────────────────────────────────────────────
print("\n=== VALID SEED GEOMETRY DISTRIBUTIONS ===")
v_ramp = stats([g["ramp_angle"] for g in valid_geoms], "ramp_angle")
v_plat = stats([g["platform_angle"] for g in valid_geoms], "platform_angle")
v_gbx = stats([g["green_ball_x"] for g in valid_geoms], "green_ball_x")
v_bkx = stats([g["basket_x"] for g in valid_geoms], "basket_x")
v_dx = stats([g["dx_basket_green"] for g in valid_geoms], "dx_basket_green(basket-green)")
v_gbr = stats([g["green_ball_radius"] for g in valid_geoms], "green_ball_radius")
v_floor_dist = stats([g["floor_distance"] for g in valid_geoms], "floor_distance")

print("\n=== IMPOSSIBLE SEED GEOMETRY DISTRIBUTIONS ===")
i_ramp = stats([g["ramp_angle"] for g in impossible_geoms], "ramp_angle")
i_plat = stats([g["platform_angle"] for g in impossible_geoms], "platform_angle")
i_gbx = stats([g["green_ball_x"] for g in impossible_geoms], "green_ball_x")
i_bkx = stats([g["basket_x"] for g in impossible_geoms], "basket_x")
i_dx = stats([g["dx_basket_green"] for g in impossible_geoms], "dx_basket_green(basket-green)")
i_gbr = stats([g["green_ball_radius"] for g in impossible_geoms], "green_ball_radius")
i_floor_dist = stats([g["floor_distance"] for g in impossible_geoms], "floor_distance")


# ── Histogram analysis: ramp_angle bins ──────────────────────────────────────
print("\n=== SOLVABILITY BY RAMP_ANGLE BIN ===")
bins = np.arange(45, 61, 1.5)
bin_labels = [(bins[i], bins[i+1]) for i in range(len(bins)-1)]

# Count valid seeds per bin
valid_ramps = np.array([g["ramp_angle"] for g in valid_geoms])
# All seeds: approximate from proportional distribution (uniform ramp_angle draw)
# Use the full valid+impossible counts to estimate marginal solvability
all_geoms_sample = valid_geoms + impossible_geoms

for lo, hi in bin_labels:
    n_valid_in_bin = np.sum((valid_ramps >= lo) & (valid_ramps < hi))
    # Estimate total seeds in this bin from the full bundle proportionally
    # Valid rate is 8.3%, so approximately n_valid / 0.083 total seeds in bin
    # But we can also look at just our sample
    all_in_bin = sum(1 for g in all_geoms_sample if lo <= g["ramp_angle"] < hi)
    rate = n_valid_in_bin / all_in_bin if all_in_bin > 0 else 0
    print(f"  ramp_angle [{lo:.1f}, {hi:.1f}): {n_valid_in_bin} valid / {all_in_bin} total = {rate:.1%}")


# ── Histogram analysis: platform_angle bins ───────────────────────────────────
print("\n=== SOLVABILITY BY PLATFORM_ANGLE BIN ===")
plat_bins = np.arange(-10, 11, 2)
plat_bin_labels = [(plat_bins[i], plat_bins[i+1]) for i in range(len(plat_bins)-1)]

valid_plats = np.array([g["platform_angle"] for g in valid_geoms])
for lo, hi in plat_bin_labels:
    n_valid_in_bin = np.sum((valid_plats >= lo) & (valid_plats < hi))
    all_in_bin = sum(1 for g in all_geoms_sample if lo <= g["platform_angle"] < hi)
    rate = n_valid_in_bin / all_in_bin if all_in_bin > 0 else 0
    print(f"  platform_angle [{lo:.1f}, {hi:.1f}): {n_valid_in_bin} valid / {all_in_bin} total = {rate:.1%}")


# ── 2D joint distribution ─────────────────────────────────────────────────────
print("\n=== JOINT (ramp_angle, platform_angle) SOLVABILITY ===")
ramp_bins = [(45, 50), (50, 52.5), (52.5, 55), (55, 57.5), (57.5, 60)]
plat_bins_2d = [(-10, -5), (-5, 0), (0, 5), (5, 10)]

print("ramp_angle \\ platform_angle | -10..-5 | -5..0 | 0..5 | 5..10")
for rlo, rhi in ramp_bins:
    row = []
    for plo, phi in plat_bins_2d:
        n_v = sum(1 for g in valid_geoms if rlo <= g["ramp_angle"] < rhi and plo <= g["platform_angle"] < phi)
        n_all = sum(1 for g in all_geoms_sample if rlo <= g["ramp_angle"] < rhi and plo <= g["platform_angle"] < phi)
        rate = n_v / n_all if n_all > 0 else float("nan")
        row.append(f"{rate:.0%}({n_all})")
    print(f"  [{rlo:.1f},{rhi:.1f}) | {' | '.join(row)}")


# ── Find the basket alignment relative to green_ball ─────────────────────────
print("\n=== BASKET-GREEN_BALL ALIGNMENT ===")
print("For valid seeds:")
stats([g["dx_basket_green"] for g in valid_geoms], "dx (basket_x - green_ball_x)")
print("For impossible seeds:")
stats([g["dx_basket_green"] for g in impossible_geoms], "dx (basket_x - green_ball_x)")


# ── Test redesign hypotheses with actual oracle ───────────────────────────────
print("\n\n=== EMPIRICAL SOLVABILITY TEST ===")

config = SimulationConfig()
_ORACLE_RNG_SALT = 630


def test_solvability_batch(seeds, variant_fn=None, n_attempts=50, oracle_steps=500, label=""):
    """Test solvability of a batch of seeds using the oracle.

    variant_fn: if provided, called with seed to get variant (default 0).
    """
    from interphyre.validation.oracles.just_a_nudge import solver as just_a_nudge_solver

    n_solved = 0
    n_total = len(seeds)
    for i, seed in enumerate(seeds):
        variant = variant_fn(seed) if variant_fn else 0
        level = load_level("just_a_nudge", seed=seed, variant=variant)
        rng = np.random.default_rng([seed, variant, _ORACLE_RNG_SALT])
        result = just_a_nudge_solver(level, config, n_attempts, oracle_steps, rng)
        if result is not None:
            n_solved += 1
        if (i + 1) % 20 == 0:
            print(f"  [{label}] {i+1}/{n_total}: {n_solved}/{i+1} = {n_solved/(i+1):.1%}")
    rate = n_solved / n_total
    print(f"  [{label}] FINAL: {n_solved}/{n_total} = {rate:.1%}")
    return rate


# Sample 100 seeds from the full range [0, 9999] to test current baseline
rng_test = np.random.default_rng(42)
test_seeds_baseline = rng_test.integers(0, 10000, size=100).tolist()

print("\n--- Baseline: 100 random seeds, current level ---")
baseline_rate = test_solvability_batch(test_seeds_baseline, label="baseline")


# ── Test redesign option A: constrain ramp_angle to [52, 58] ─────────────────
# Monkey-patch the level builder to use a narrower ramp_angle range.
# We do this by patching np.random.Generator.uniform at the call site,
# which is tricky. Instead, use a cleaner approach: override just the
# ramp_angle draw by post-hoc filtering seeds that would produce ramp_angle
# in the target range, OR by modifying the level at the module level temporarily.

print("\n--- Redesign A: narrow ramp_angle to [52, 58] ---")
print("(Testing seeds that naturally fall in this ramp_angle range from the bundle)")

# From the valid bundle: find seeds with ramp_angle in [52, 58]
import interphyre.levels.just_a_nudge as jan_module

_original_build = jan_module.build_level.__wrapped__ if hasattr(jan_module.build_level, '__wrapped__') else None

# Approach: temporarily replace the ramp_angle draw by monkey-patching rng.uniform
# We'll use a wrapper that intercepts the 3rd uniform draw (ramp_angle = 3rd call)
# Instead, let's use a simpler approach: directly reconstruct geometry for many seeds
# to filter for those that would be valid under the new constraint.

# For a proper test, we simulate: "if we changed ramp_angle range to [52, 58],
# what fraction of seeds (re-drawn) would be solvable?"
# The oracle doesn't care about how the seed was generated — it just runs on the level.
# But the level GEOMETRY is determined by the seed.
# A proper redesign test: draw 100 new random levels where ramp_angle is forced to [52, 58].

# We test by drawing seeds and checking their ramp_angle, then only testing
# seeds whose ramp_angle falls naturally in [52, 58]:
seeds_narrow_ramp = [
    e["seed"] for e in all_entries[:2000]
    if extract_geometry(e["seed"], e.get("variant", 0))["ramp_angle"] >= 52
    and extract_geometry(e["seed"], e.get("variant", 0))["ramp_angle"] <= 58
]
print(f"Seeds with ramp_angle in [52, 58]: {len(seeds_narrow_ramp)} out of first 2000")

# Sample 100 of those seeds for testing
rng_a = np.random.default_rng(7)
test_seeds_a = rng_a.choice(seeds_narrow_ramp[:200], size=min(100, len(seeds_narrow_ramp)), replace=False).tolist()
print(f"Testing {len(test_seeds_a)} seeds with natural ramp_angle in [52, 58]...")
rate_a = test_solvability_batch(test_seeds_a, label="ramp52-58")


# ── Test redesign option B: narrow ramp_angle to [50, 57] ─────────────────────
print("\n--- Redesign B: narrow ramp_angle to [50, 57] ---")
seeds_b = [
    e["seed"] for e in all_entries[:3000]
    if 50 <= extract_geometry(e["seed"], e.get("variant", 0))["ramp_angle"] <= 57
]
print(f"Seeds with ramp_angle in [50, 57]: {len(seeds_b)} out of first 3000")
rng_b = np.random.default_rng(13)
test_seeds_b = rng_b.choice(seeds_b[:200], size=min(100, len(seeds_b)), replace=False).tolist()
print(f"Testing {len(test_seeds_b)} seeds with natural ramp_angle in [50, 57]...")
rate_b = test_solvability_batch(test_seeds_b, label="ramp50-57")


# ── Test redesign option C: positive platform_angle only [0, 10] ───────────────
print("\n--- Redesign C: platform_angle restricted to [0, 10] ---")
seeds_c = [
    e["seed"] for e in all_entries[:3000]
    if extract_geometry(e["seed"], e.get("variant", 0))["platform_angle"] >= 0
]
print(f"Seeds with platform_angle in [0, 10]: {len(seeds_c)} out of first 3000")
rng_c = np.random.default_rng(17)
test_seeds_c = rng_c.choice(seeds_c[:200], size=min(100, len(seeds_c)), replace=False).tolist()
print(f"Testing {len(test_seeds_c)} seeds with natural platform_angle in [0, 10]...")
rate_c = test_solvability_batch(test_seeds_c, label="plat0-10")


# ── Test combo: ramp [52,58] AND platform_angle >= 0 ──────────────────────────
print("\n--- Redesign D: ramp_angle [52,58] AND platform_angle [0, 10] ---")
seeds_d = [
    e["seed"] for e in all_entries[:4000]
    if 52 <= extract_geometry(e["seed"], e.get("variant", 0))["ramp_angle"] <= 58
    and extract_geometry(e["seed"], e.get("variant", 0))["platform_angle"] >= 0
]
print(f"Seeds matching combo: {len(seeds_d)} out of first 4000")
rng_d = np.random.default_rng(23)
test_seeds_d = rng_d.choice(seeds_d[:200], size=min(100, len(seeds_d)), replace=False).tolist()
print(f"Testing {len(test_seeds_d)} seeds with ramp [52,58] AND plat [0,10]...")
rate_d = test_solvability_batch(test_seeds_d, label="combo-D")


# ── Summary ───────────────────────────────────────────────────────────────────
print("\n\n=== SUMMARY ===")
print(f"Baseline (current level, random seeds):  {baseline_rate:.1%}")
print(f"Option A (ramp_angle in [52, 58]):        {rate_a:.1%}")
print(f"Option B (ramp_angle in [50, 57]):        {rate_b:.1%}")
print(f"Option C (platform_angle in [0, 10]):     {rate_c:.1%}")
print(f"Option D (ramp [52,58] + plat [0,10]):    {rate_d:.1%}")
