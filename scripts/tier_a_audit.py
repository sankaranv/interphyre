"""Solvability audit for 7 near-100% levels.

For each level:
  1. Load impossible seeds from bundle.
  2. Test false negative rate with n_attempts=500 on first 20 impossible seeds.
  3. Inspect geometry of impossible vs valid seeds.
"""

from __future__ import annotations
import json, lzma, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from interphyre.config import SimulationConfig
from interphyre.levels import load_level
from interphyre.validation import _ORACLE_RNG_SALT
from interphyre.validation.oracles import get_oracle

LEVELS_DIR = Path(__file__).parent.parent / "interphyre" / "data" / "levels"
RESULTS_DIR = Path(__file__).parent.parent / "results" / "solvability_audit"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TARGET_LEVELS = [
    "off_the_rails",
    "straight_face",
    "pass_the_parcel",
    "falling_into_place",
    "mind_the_gap",
    "dive_bomb",
    "keyhole",
]

config = SimulationConfig()


def load_bundle(level_name):
    bundle_path = LEVELS_DIR / f"{level_name}.json.lzma"
    with lzma.open(bundle_path, "rt") as f:
        data = json.load(f)
    impossible = [e for e in data["entries"] if e["status"] == "impossible"]
    valid = [e for e in data["entries"] if e["status"] == "valid"]
    return impossible, valid


def false_negative_rate(level_name, impossible, n_sample=20, n_attempts=500):
    oracle_fn = get_oracle(level_name)
    sample = impossible[:n_sample]
    recovered = 0
    for entry in sample:
        seed = entry["seed"]
        for variant in range(10):
            level = load_level(level_name, seed=seed, variant=variant)
            rng = np.random.default_rng([seed, variant, _ORACLE_RNG_SALT])
            if oracle_fn(level, config, n_attempts=n_attempts, oracle_steps=500, rng=rng):
                recovered += 1
                break
        sys.stdout.write(".")
        sys.stdout.flush()
    print()
    return recovered, len(sample)


def geometry_stats(level_name, impossible, valid, n_sample=5):
    stats = {"impossible": [], "valid": []}
    for group_name, group in [("impossible", impossible[:n_sample]), ("valid", valid[:n_sample])]:
        for entry in group:
            seed = entry["seed"]
            variant = entry.get("variant", 0)
            try:
                level = load_level(level_name, seed=seed, variant=variant)
                obj_stats = {}
                for name, obj in level.objects.items():
                    od = {"x": float(obj.x), "y": float(obj.y)}
                    for attr in ("radius", "length", "angle"):
                        if hasattr(obj, attr):
                            od[attr] = float(getattr(obj, attr))
                    obj_stats[name] = od
                stats[group_name].append({"seed": seed, "objects": obj_stats})
            except Exception as e:
                stats[group_name].append({"seed": seed, "error": str(e)})
    return stats


def summarize_geometry(level_name, geom):
    lines = [f"\n--- Geometry diff: {level_name} ---"]
    imp_entries = [e for e in geom["impossible"] if "objects" in e]
    val_entries = [e for e in geom["valid"] if "objects" in e]
    if not imp_entries or not val_entries:
        return "\n".join(lines)
    obj_names = list(imp_entries[0]["objects"].keys())
    for obj_name in obj_names:
        imp_vals = [e["objects"][obj_name] for e in imp_entries if obj_name in e["objects"]]
        val_vals = [e["objects"][obj_name] for e in val_entries if obj_name in e["objects"]]
        if not imp_vals or not val_vals:
            continue
        all_attrs = sorted(set(imp_vals[0].keys()))
        diffs = []
        for attr in all_attrs:
            iv = [v[attr] for v in imp_vals if attr in v]
            vv = [v[attr] for v in val_vals if attr in v]
            if not iv or not vv:
                continue
            im, vm = np.mean(iv), np.mean(vv)
            if abs(im - vm) > 0.05:
                diffs.append(f"  {attr}: imp={im:.3f}[{min(iv):.2f},{max(iv):.2f}]  val={vm:.3f}[{min(vv):.2f},{max(vv):.2f}]")
        if diffs:
            lines.append(f"  {obj_name}:")
            lines.extend(diffs)
    return "\n".join(lines)


if __name__ == "__main__":
    results = {}
    for level_name in TARGET_LEVELS:
        print(f"\n{'='*60}\nAUDITING: {level_name}")
        impossible, valid = load_bundle(level_name)
        print(f"  Bundle: {len(impossible)} impossible, {len(valid)} valid")
        n_sample = min(20, len(impossible))
        if n_sample == 0:
            fn_rec, fn_n = 0, 0
            print("  No impossible seeds — skipping FN test")
        else:
            print(f"  FN test (n_attempts=500, n_sample={n_sample})...")
            fn_rec, fn_n = false_negative_rate(level_name, impossible, n_sample)
            print(f"  FN recovered: {fn_rec}/{fn_n} ({100*fn_rec/fn_n:.1f}%)")

        geom = geometry_stats(level_name, impossible, valid, n_sample=5)
        print(summarize_geometry(level_name, geom))

        results[level_name] = {
            "n_impossible": len(impossible),
            "n_valid": len(valid),
            "fn_rec": fn_rec,
            "fn_n": fn_n,
            "fn_rate": fn_rec / fn_n if fn_n > 0 else 0.0,
            "geometry": geom,
        }

    # Save raw results
    saveable = {k: {ek: ev for ek, ev in v.items() if ek != "geometry"}
                for k, v in results.items()}
    out_path = RESULTS_DIR / "tier_a_raw.json"
    with open(out_path, "w") as f:
        json.dump(saveable, f, indent=2)
    print(f"\nSaved summary to {out_path}")
