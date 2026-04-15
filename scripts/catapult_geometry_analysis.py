"""
Catapult geometric constraint analysis.

After the v5 parameter fixes, the 253 impossible seeds no longer cluster
around any single parameter. This script investigates derived geometric
features — the relationship between arm_right, launch height, and basket
position — to find a trajectory-based constraint.

Hypothesis: impossibility is determined by whether the catapult's maximum
achievable projectile range can reach the basket at (3.5, ledge_center_y).
The green ball launches from approximately (arm_right, arm_top) and must
reach (3.5, ledge_center_y). The basket is ALWAYS at x=3.5.
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
N_VALID_SAMPLE = 500


def extract_geometry(level) -> dict:
    """Extract launch geometry and basket position for trajectory analysis."""
    red_ball = level.objects["red_ball"]
    gray_platform = level.objects["gray_platform"]
    gray_ball = level.objects["gray_ball"]
    ledge = level.objects["ledge"]
    basket = level.objects["basket"]
    black_platform = level.objects["black_platform"]
    green_ball = level.objects["green_ball"]

    arm_right = gray_platform.x + gray_platform.length / 2
    arm_top = gray_platform.y + gray_platform.thickness / 2  # launch height approx

    # Horizontal distance from arm tip to basket center
    horiz_dist = 3.5 - arm_right

    # Vertical drop from arm tip to basket (positive = basket below arm)
    vert_drop = arm_top - ledge.y  # positive when basket is below launch height

    # Flight angle needed (degrees from horizontal, negative = downward)
    # For a parabolic trajectory with no drag: range = v² sin(2θ) / g
    # We need to reach (horiz_dist, -vert_drop) from origin
    # The key ratio: vert_drop / horiz_dist (negative = basket is below, positive = above)
    trajectory_slope = -vert_drop / horiz_dist if horiz_dist > 0 else np.nan

    # Basket scale determines target size and blue_ball mass
    basket_scale = basket.scale

    # Combined "reachability" score: larger = more favorable for solvability
    # arm_right contributes positively (shorter flight), vert_drop positively (gravity helps)
    # Both should be positive for a reasonable trajectory
    reachability = arm_right + vert_drop / 4.0  # rough heuristic

    return {
        "red_ball_radius": red_ball.radius,
        "arm_right": arm_right,
        "arm_top": arm_top,
        "ledge_center_y": ledge.y,
        "basket_scale": basket_scale,
        "horiz_dist": horiz_dist,
        "vert_drop": vert_drop,
        "trajectory_slope": trajectory_slope,
        "reachability": reachability,
        "arm_right_over_horiz": arm_right / horiz_dist if horiz_dist > 0 else np.nan,
    }


def threshold_analysis(label, imp_vals, val_vals, thresholds, direction="below"):
    """Print threshold analysis for a feature (direction: 'below' or 'above')."""
    print(f"\n  Threshold analysis: {label}")
    print(f"  {'Threshold':>12}  {'%imp excl':>10}  {'%val excl':>10}  {'ratio':>8}")
    for t in thresholds:
        if direction == "below":
            imp_excl = (imp_vals < t).mean() * 100
            val_excl = (val_vals < t).mean() * 100
        else:
            imp_excl = (imp_vals > t).mean() * 100
            val_excl = (val_vals > t).mean() * 100
        ratio = imp_excl / val_excl if val_excl > 0 else np.inf
        marker = "  *" if ratio >= 3.0 and imp_excl >= 50 else ""
        print(f"  {t:>12.3f}  {imp_excl:>10.1f}  {val_excl:>10.1f}  {ratio:>8.2f}{marker}")


def main():
    print("Loading bundle...", flush=True)
    with lzma.open(BUNDLE_PATH) as f:
        bundle = json.load(f)

    entries = bundle["entries"]
    impossible_seeds = sorted({e["seed"] for e in entries if e["status"] == "impossible"})
    valid_seeds = [e["seed"] for e in entries if e["status"] == "valid"]
    print(
        f"Bundle: {len(entries)} total, {len(valid_seeds)} valid, "
        f"{len(impossible_seeds)} impossible\n",
        flush=True,
    )

    rng_sample = random.Random(42)
    valid_sample = rng_sample.sample(valid_seeds, min(N_VALID_SAMPLE, len(valid_seeds)))

    print(f"Loading {len(impossible_seeds)} impossible seed geometries...", flush=True)
    impossible_geom = []
    for i, seed in enumerate(impossible_seeds):
        if i % 50 == 0:
            print(f"  {i}/{len(impossible_seeds)}", flush=True)
        level = load_level("catapult", seed=seed, variant=0)
        impossible_geom.append(extract_geometry(level))

    print(f"Loading {len(valid_sample)} valid seed geometries...", flush=True)
    valid_geom = []
    for i, seed in enumerate(valid_sample):
        if i % 100 == 0:
            print(f"  {i}/{len(valid_sample)}", flush=True)
        level = load_level("catapult", seed=seed, variant=0)
        valid_geom.append(extract_geometry(level))

    features = [
        "arm_right", "arm_top", "horiz_dist", "vert_drop",
        "trajectory_slope", "reachability", "arm_right_over_horiz",
        "basket_scale", "red_ball_radius",
    ]

    print("\n" + "=" * 70)
    print("DERIVED GEOMETRIC FEATURES: IMPOSSIBLE vs VALID")
    print("=" * 70)

    for feat in features:
        imp_vals = np.array([g[feat] for g in impossible_geom if not np.isnan(g[feat])])
        val_vals = np.array([g[feat] for g in valid_geom if not np.isnan(g[feat])])
        diff = imp_vals.mean() - val_vals.mean()
        pooled_std = (imp_vals.std() + val_vals.std()) / 2
        effect_size = diff / pooled_std if pooled_std > 0 else 0
        print(
            f"  {feat:<30} imp={imp_vals.mean():7.3f}±{imp_vals.std():.3f}  "
            f"val={val_vals.mean():7.3f}±{val_vals.std():.3f}  "
            f"d={effect_size:+.2f}"
        )

    # ---- Detailed threshold analysis for the most discriminating features ----
    print("\n" + "=" * 70)
    print("THRESHOLD ANALYSIS (ratio = imp_excl% / val_excl%; * = ratio>=3 and imp>=50%)")
    print("=" * 70)

    imp_arm = np.array([g["arm_right"] for g in impossible_geom])
    val_arm = np.array([g["arm_right"] for g in valid_geom])
    threshold_analysis(
        "arm_right (below threshold → exclude)",
        imp_arm, val_arm,
        [0.80, 0.85, 0.875, 0.90, 0.925, 0.95, 0.975, 1.00],
        direction="below",
    )

    imp_vd = np.array([g["vert_drop"] for g in impossible_geom])
    val_vd = np.array([g["vert_drop"] for g in valid_geom])
    threshold_analysis(
        "vert_drop = arm_top - ledge_y (below → exclude; more drop = harder)",
        imp_vd, val_vd,
        [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
        direction="below",
    )

    imp_reach = np.array([g["reachability"] for g in impossible_geom])
    val_reach = np.array([g["reachability"] for g in valid_geom])
    threshold_analysis(
        "reachability = arm_right + vert_drop/4 (below → exclude)",
        imp_reach, val_reach,
        [1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8],
        direction="below",
    )

    # ---- Joint constraint: arm_right AND vert_drop ----
    print("\n" + "=" * 70)
    print("JOINT CONSTRAINT: arm_right < A AND vert_drop < V")
    print("(impossible seed if BOTH conditions met → potential exclusion zone)")
    print("=" * 70)
    imp_arm = np.array([g["arm_right"] for g in impossible_geom])
    imp_vd = np.array([g["vert_drop"] for g in impossible_geom])
    val_arm = np.array([g["arm_right"] for g in valid_geom])
    val_vd = np.array([g["vert_drop"] for g in valid_geom])

    print(f"  {'arm_thresh':>10} {'vd_thresh':>10} {'%imp':>8} {'%val':>8} {'ratio':>8}")
    for a_thresh in [0.90, 0.95, 1.00]:
        for v_thresh in [3.0, 3.5, 4.0, 4.5]:
            imp_excl = ((imp_arm < a_thresh) | (imp_vd < v_thresh)).mean() * 100
            val_excl = ((val_arm < a_thresh) | (val_vd < v_thresh)).mean() * 100
            ratio = imp_excl / val_excl if val_excl > 0 else np.inf
            print(
                f"  {a_thresh:>10.2f} {v_thresh:>10.1f} "
                f"{imp_excl:>8.1f} {val_excl:>8.1f} {ratio:>8.2f}"
            )

    # ---- Summary: what fraction of impossible seeds lie in the most discriminating region? ----
    print("\n" + "=" * 70)
    print("DISTRIBUTION PERCENTILES FOR arm_right")
    print("=" * 70)
    for pct in [5, 10, 15, 20, 25, 30]:
        imp_p = np.percentile(imp_arm, pct)
        val_p = np.percentile(val_arm, pct)
        print(f"  p{pct:02d}: impossible={imp_p:.3f}, valid={val_p:.3f}")

    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"  arm_right: impossible mean={imp_arm.mean():.3f}, valid mean={val_arm.mean():.3f}")
    print(f"  Effect size (Cohen's d): {(imp_arm.mean()-val_arm.mean())/((imp_arm.std()+val_arm.std())/2):.2f}")
    print(f"  vert_drop: impossible mean={imp_vd.mean():.3f}, valid mean={val_vd.mean():.3f}")
    print(f"  Effect size: {(imp_vd.mean()-val_vd.mean())/((imp_vd.std()+val_vd.std())/2):.2f}")
    print("\n  Conclusion: can a simple level parameter constraint eliminate impossible seeds?")
    print("  (ratio >=3 with >80% impossible coverage would be conclusive)")


if __name__ == "__main__":
    main()
