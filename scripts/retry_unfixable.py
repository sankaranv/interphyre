#!/usr/bin/env python3
"""Retry unfixable seeds from a previous validate_and_regen run.

For each unfixable seed, searches variants 0..max_variants-1 using load_level()
(the same path as original bundle generation). A variant change is acceptable —
the goal is a correct, committed solution for every seed that was previously
declared valid. Updates the bundle and report in-place.

Usage:
    python scripts/retry_unfixable.py --level catapult [--attempts 300] [--workers 8]
"""

from __future__ import annotations

import argparse
import json
import lzma
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

PROJECT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT))

from interphyre.config import SimulationConfig
from interphyre.levels import load_level
from interphyre.validation._bundle import _BUNDLE_DIR, _oracle_rng
from interphyre.validation.checks import extract_scene_dict, is_trivial
from interphyre.validation.oracles import get_default_max_variants, get_solver


def _retry_seed(args: tuple) -> dict:
    """Worker: search all variants for a solution. Mirrors _validate_seed in _bundle.py."""
    level_name, seed, n_attempts, max_variants = args
    config = SimulationConfig()
    solver = get_solver(level_name)

    if solver is None:
        return {"seed": seed, "status": "unfixable", "variant": None,
                "scene": None, "solution": None}

    for variant in range(max_variants):
        level = load_level(level_name, seed=seed, variant=variant)
        if is_trivial(level, config):
            continue

        rng = _oracle_rng(seed, variant)
        sol = solver(level, config, n_attempts, oracle_steps=1000, rng=rng)
        if sol is not None:
            scene_dict = extract_scene_dict(level)
            solution_json = [[p[0], p[1], p[2]] for p in sol]
            return {
                "seed": seed,
                "status": "fixed",
                "variant": variant,
                "scene": scene_dict,
                "solution": solution_json,
            }

    return {"seed": seed, "status": "unfixable", "variant": None,
            "scene": None, "solution": None}


def retry_unfixable(level_name: str, n_attempts: int, workers: int, max_variants: int | None = None) -> None:
    report_path = PROJECT / "scratch" / "bundle_regen" / f"{level_name}_report.json"
    if not report_path.exists():
        raise FileNotFoundError(f"No report found: {report_path}")

    with open(report_path) as fh:
        report = json.load(fh)

    unfixable_seeds = report["unfixable"]
    if not unfixable_seeds:
        print(f"[{level_name}] No unfixable seeds — nothing to do.")
        return

    if max_variants is None:
        max_variants = get_default_max_variants(level_name)
    print(
        f"[{level_name}] Retrying {len(unfixable_seeds)} unfixable seeds: "
        f"{n_attempts} attempts × {max_variants} variants each ({workers} workers)..."
    )

    bundle_path = _BUNDLE_DIR / f"{level_name}.json.lzma"
    with lzma.open(bundle_path, "rb") as fh:
        bundle = json.load(fh)

    entries = bundle["entries"]

    work = [
        (level_name, seed, n_attempts, max_variants)
        for seed in unfixable_seeds
    ]

    fixed = []
    still_unfixable = []

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_retry_seed, args): args[1] for args in work}
        for future in as_completed(futures):
            result = future.result()
            if result["status"] == "fixed":
                fixed.append(result)
                print(f"  seed {result['seed']}: FIXED at variant={result['variant']} "
                      f"→ {result['solution']}")
            else:
                still_unfixable.append(result["seed"])
                print(f"  seed {result['seed']}: still unfixable after {max_variants} variants")

    # Patch bundle entries for fixed seeds.
    if fixed:
        fixed_map = {r["seed"]: r for r in fixed}
        for entry in entries:
            if entry["seed"] in fixed_map and entry["status"] == "valid":
                fix = fixed_map[entry["seed"]]
                entry["variant"] = fix["variant"]
                entry["scene"] = fix["scene"]
                entry["solution"] = fix["solution"]
        tmp = bundle_path.with_suffix(".lzma.tmp")
        with lzma.open(tmp, "wt", encoding="utf-8") as fh:
            json.dump(bundle, fh)
        tmp.replace(bundle_path)
        print(f"[{level_name}] Bundle updated: {len(fixed)} seeds re-solved "
              f"(variant, scene, and solution replaced where needed).")

    # Update report.
    report["fixed"] = report.get("fixed", 0) + len(fixed)
    report["unfixable"] = sorted(still_unfixable)
    with open(report_path, "w") as fh:
        json.dump(report, fh, indent=2)

    print(f"[{level_name}] Done. newly_fixed={len(fixed)}, "
          f"still_unfixable={len(still_unfixable)}.")
    if still_unfixable:
        print(f"  Still unfixable: {still_unfixable}")
        sys.exit(1)
    sys.exit(0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", required=True)
    parser.add_argument(
        "--attempts", type=int, default=300,
        help="Oracle attempts per variant (default: 300, matching original generation)",
    )
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max-variants", type=int, default=None,
                        help="Override max variants to search (default: oracle's registered value)")
    args = parser.parse_args()
    retry_unfixable(args.level, args.attempts, args.workers, args.max_variants)


if __name__ == "__main__":
    main()
