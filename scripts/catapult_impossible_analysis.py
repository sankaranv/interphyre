"""
Catapult impossible seed parameter analysis.

Load the catapult v5 bundle, identify all 253 impossible seeds, regenerate
their level configurations, and compare parameter distributions against a
sample of valid seeds. Determines the tightest single-parameter threshold
for eliminating impossible seeds with minimal valid-seed collateral loss.

The leading hypothesis: red_ball_radius < 0.9 is the primary driver
(log-OR = 2.47; r<0.75 has ~1.5% solvability in prior grid audit).
"""

import json
import lzma
import random
import sys

import numpy as np

sys.path.insert(0, "/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre")
from interphyre.levels import load_level  # noqa: E402

BUNDLE_PATH = (
    "/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre"
    "/interphyre/data/levels/catapult.json.lzma"
)
# Match the number of impossible seeds for a fair comparison
N_VALID_SAMPLE = 500


def extract_params(level) -> dict:
    """Extract the four solvability-relevant parameters from a catapult level."""
    red_ball = level.objects["red_ball"]
    gray_platform = level.objects["gray_platform"]
    ledge = level.objects["ledge"]
    basket = level.objects["basket"]
    arm_right = gray_platform.x + gray_platform.length / 2
    return {
        "red_ball_radius": red_ball.radius,
        "arm_right": arm_right,
        "ledge_center_y": ledge.y,
        "basket_scale": basket.scale,
    }


def main():
    print("Loading bundle...", flush=True)
    with lzma.open(BUNDLE_PATH) as f:
        bundle = json.load(f)

    entries = bundle["entries"]
    impossible_seeds = sorted({e["seed"] for e in entries if e["status"] == "impossible"})
    valid_seeds = [e["seed"] for e in entries if e["status"] == "valid"]
    print(
        f"Bundle: {len(entries)} total, {len(valid_seeds)} valid, "
        f"{len(impossible_seeds)} impossible",
        flush=True,
    )

    # Sample valid seeds for comparison
    rng_sample = random.Random(42)
    valid_sample = rng_sample.sample(valid_seeds, min(N_VALID_SAMPLE, len(valid_seeds)))

    # Load level configs for all impossible seeds
    print(f"\nLoading {len(impossible_seeds)} impossible seed configurations...", flush=True)
    impossible_params = []
    for i, seed in enumerate(impossible_seeds):
        if i % 50 == 0:
            print(f"  {i}/{len(impossible_seeds)}", flush=True)
        level = load_level("catapult", seed=seed, variant=0)
        impossible_params.append(extract_params(level))

    # Load level configs for valid sample
    print(f"\nLoading {len(valid_sample)} valid seed configurations...", flush=True)
    valid_params = []
    for i, seed in enumerate(valid_sample):
        if i % 100 == 0:
            print(f"  {i}/{len(valid_sample)}", flush=True)
        level = load_level("catapult", seed=seed, variant=0)
        valid_params.append(extract_params(level))

    # --- Distribution comparison ---
    print("\n" + "=" * 60)
    print("PARAMETER DISTRIBUTIONS: IMPOSSIBLE vs VALID SEEDS")
    print("=" * 60)

    for key in ["red_ball_radius", "arm_right", "ledge_center_y", "basket_scale"]:
        imp_vals = np.array([p[key] for p in impossible_params])
        val_vals = np.array([p[key] for p in valid_params])
        print(f"\n--- {key} ---")
        print(
            f"  Impossible ({len(imp_vals)}): "
            f"mean={imp_vals.mean():.3f}, std={imp_vals.std():.3f}, "
            f"p10={np.percentile(imp_vals, 10):.3f}, "
            f"p50={np.percentile(imp_vals, 50):.3f}, "
            f"p90={np.percentile(imp_vals, 90):.3f}"
        )
        print(
            f"  Valid ({len(val_vals)}): "
            f"mean={val_vals.mean():.3f}, std={val_vals.std():.3f}, "
            f"p10={np.percentile(val_vals, 10):.3f}, "
            f"p50={np.percentile(val_vals, 50):.3f}, "
            f"p90={np.percentile(val_vals, 90):.3f}"
        )

    # --- Threshold analysis for red_ball_radius ---
    print("\n" + "=" * 60)
    print("THRESHOLD ANALYSIS: red_ball_radius lower bound")
    print("Columns: threshold | %impossible eliminated | %valid excluded")
    print("=" * 60)
    imp_r = np.array([p["red_ball_radius"] for p in impossible_params])
    val_r = np.array([p["red_ball_radius"] for p in valid_params])
    best_threshold = None
    for threshold in [0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]:
        pct_imp_below = (imp_r < threshold).mean() * 100
        pct_val_below = (val_r < threshold).mean() * 100
        marker = ""
        # Prefer threshold that eliminates >=80% of impossible with <=5% valid exclusion
        if pct_imp_below >= 80 and pct_val_below <= 5:
            marker = "  <-- CANDIDATE"
            if best_threshold is None:
                best_threshold = threshold
        print(
            f"  r < {threshold:.2f}: {pct_imp_below:5.1f}% impossible excluded, "
            f"{pct_val_below:5.1f}% valid excluded{marker}"
        )

    # --- Threshold analysis for arm_right ---
    print("\n" + "=" * 60)
    print("THRESHOLD ANALYSIS: arm_right lower bound")
    print("=" * 60)
    imp_arm = np.array([p["arm_right"] for p in impossible_params])
    val_arm = np.array([p["arm_right"] for p in valid_params])
    for threshold in [0.80, 0.85, 0.90, 0.95, 1.00, 1.05]:
        pct_imp_below = (imp_arm < threshold).mean() * 100
        pct_val_below = (val_arm < threshold).mean() * 100
        print(
            f"  arm_right < {threshold:.2f}: {pct_imp_below:5.1f}% impossible excluded, "
            f"{pct_val_below:5.1f}% valid excluded"
        )

    # --- Joint analysis: red_ball_radius AND arm_right ---
    print("\n" + "=" * 60)
    print("JOINT THRESHOLD ANALYSIS: r < T1 OR arm_right < T2")
    print("(seeds excluded if EITHER condition is met)")
    print("=" * 60)
    for r_thresh in [0.85, 0.90]:
        for arm_thresh in [0.85, 0.90]:
            imp_excluded = (
                (imp_r < r_thresh) | (imp_arm < arm_thresh)
            ).mean() * 100
            val_excluded = (
                (val_r < r_thresh) | (val_arm < arm_thresh)
            ).mean() * 100
            print(
                f"  r<{r_thresh:.2f} OR arm_right<{arm_thresh:.2f}: "
                f"{imp_excluded:5.1f}% impossible excluded, "
                f"{val_excluded:5.1f}% valid excluded"
            )

    # --- Recommendation ---
    print("\n" + "=" * 60)
    print("RECOMMENDATION")
    print("=" * 60)
    if best_threshold is not None:
        excluded_valid_pct = (val_r < best_threshold).mean() * 100
        excluded_impossible_pct = (imp_r < best_threshold).mean() * 100
        remaining_impossible = len(impossible_seeds) * (1 - excluded_impossible_pct / 100)
        print(
            f"  Raise red_ball_radius lower bound to {best_threshold:.2f}"
        )
        print(
            f"  This excludes {excluded_impossible_pct:.1f}% of impossible seeds "
            f"({excluded_impossible_pct / 100 * len(impossible_seeds):.0f} of {len(impossible_seeds)})"
        )
        print(
            f"  And {excluded_valid_pct:.1f}% of valid seeds "
            f"({excluded_valid_pct / 100 * len(valid_seeds):.0f} of {len(valid_seeds)}) — "
            f"these seeds will be regenerated with new parameter"
        )
        print(f"  Estimated remaining impossible seeds after fix: ~{remaining_impossible:.0f}")
    else:
        print(
            "  No single red_ball_radius threshold gives >=80% impossible elimination "
            "with <=5% valid exclusion."
        )
        print(
            "  Consider joint constraint on (red_ball_radius, arm_right). "
            "Review joint analysis table above."
        )


if __name__ == "__main__":
    main()
