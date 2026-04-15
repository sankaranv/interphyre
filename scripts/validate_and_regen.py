#!/usr/bin/env python3
"""Validate a level's bundle against env.step() and regenerate any failing seeds.

For each seed with status="valid" in the bundle:
  1. Replay the stored solution via InterphyreEnv.reset() + env.step().
  2. If it fails, run the solver on the same scene to find a replacement.
  3. If a replacement is found, update the bundle entry in-place.

Output written to scratch/bundle_regen/<level_name>_report.json:
  {
    "level_name": str,
    "total_valid": int,
    "passed": int,
    "fixed": int,
    "unfixable": [seed, ...]
  }

Usage:
    python scripts/validate_and_regen.py --level basket_case [--workers 4]
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
from interphyre.environment import InterphyreEnv
from interphyre.levels import build_level_from_scene
from interphyre.validation._bundle import _BUNDLE_DIR, _oracle_rng
from interphyre.validation.checks import is_trivial
from interphyre.validation.oracles import get_oracle, get_solver

_N_ATTEMPTS_REGEN = 300  # Higher than default (50) for hard seeds


_SOLUTION_ROUND_DIGITS = 4  # Match _bundle.py: 4dp gives 0.0001 precision.


def _test_solution(level_name: str, seed: int, entry: dict) -> bool:
    """Return True if stored solution succeeds via env.step()."""
    level = build_level_from_scene(level_name, entry["scene"])
    env = InterphyreEnv(level, validate=False)
    try:
        env.reset()
        _, _, _, _, info = env.step(entry["solution"])
    finally:
        env.close()
    return info.get("success", False)


def _regen_solution(
    level_name: str, seed: int, entry: dict
) -> list[list[float]] | None:
    """Find a replacement solution for the same scene using the current oracle.

    Returns solution as [[x, y, r], ...] on success, None if unresolvable.
    """
    level = build_level_from_scene(level_name, entry["scene"])
    config = SimulationConfig()

    # Skip if trivial (success without any action — shouldn't be in bundle, but guard).
    if is_trivial(level, config):
        return None

    solver = get_solver(level_name)
    oracle = get_oracle(level_name)
    rng = _oracle_rng(seed, entry["variant"])

    if solver is not None:
        sol = solver(level, config, _N_ATTEMPTS_REGEN, oracle_steps=1000, rng=rng)
        if sol is not None:
            # Round to 4dp before storing, matching _bundle.py's rounding invariant.
            # Verify the rounded solution still solves the level — a solution that
            # fails after rounding was knife-edge and should not enter the bundle.
            solution_json = [
                [
                    round(pos[0], _SOLUTION_ROUND_DIGITS),
                    round(pos[1], _SOLUTION_ROUND_DIGITS),
                    round(pos[2], _SOLUTION_ROUND_DIGITS),
                ]
                for pos in sol
            ]
            env = InterphyreEnv(level, validate=False)
            try:
                env.reset()
                _, _, _, _, info = env.step(solution_json)
            finally:
                env.close()
            if not info.get("success", False):
                return None  # Rounded solution is knife-edge; mark as unfixable.
            return solution_json
    else:
        if oracle(level, config, _N_ATTEMPTS_REGEN, oracle_steps=1000, rng=rng):
            return None  # oracle-only level: no solution coordinates available

    return None


def _process_entry(args: tuple) -> dict:
    """Worker: test one entry and regenerate if it fails. Picklable top-level fn."""
    level_name, seed, entry = args
    passed = _test_solution(level_name, seed, entry)
    if passed:
        return {"seed": seed, "status": "pass", "solution": None}

    new_sol = _regen_solution(level_name, seed, entry)
    if new_sol is not None:
        return {"seed": seed, "status": "fixed", "solution": new_sol}

    return {"seed": seed, "status": "unfixable", "solution": None}


def validate_and_regen(level_name: str, workers: int) -> dict:
    bundle_path = _BUNDLE_DIR / f"{level_name}.json.lzma"
    if not bundle_path.exists():
        raise FileNotFoundError(f"No bundle found: {bundle_path}")

    with lzma.open(bundle_path, "rb") as fh:
        bundle = json.load(fh)

    entries = bundle["entries"]
    valid_entries = [
        (seed, e) for e in entries if e["status"] == "valid" for seed in [e["seed"]]
    ]

    print(
        f"[{level_name}] Testing {len(valid_entries)} valid entries with {workers} workers..."
    )

    results = {"pass": [], "fixed": [], "unfixable": []}
    work = [(level_name, seed, entry) for seed, entry in valid_entries]

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_process_entry, args): args[1] for args in work}
        done = 0
        for future in as_completed(futures):
            result = future.result()
            results[result["status"]].append(result)
            done += 1
            if done % 500 == 0:
                print(
                    f"[{level_name}] {done}/{len(valid_entries)} done "
                    f"(pass={len(results['pass'])}, "
                    f"fixed={len(results['fixed'])}, "
                    f"unfixable={len(results['unfixable'])})"
                )

    # Patch bundle entries for fixed seeds.
    if results["fixed"]:
        fixed_map = {r["seed"]: r["solution"] for r in results["fixed"]}
        for entry in entries:
            if entry["seed"] in fixed_map and entry["status"] == "valid":
                entry["solution"] = fixed_map[entry["seed"]]
        # Rewrite bundle.
        tmp = bundle_path.with_suffix(".lzma.tmp")
        with lzma.open(tmp, "wt", encoding="utf-8") as fh:
            json.dump(bundle, fh)
        tmp.replace(bundle_path)
        print(
            f"[{level_name}] Bundle updated with {len(results['fixed'])} fixed entries."
        )

    report = {
        "level_name": level_name,
        "total_valid": len(valid_entries),
        "passed": len(results["pass"]),
        "fixed": len(results["fixed"]),
        "unfixable": [r["seed"] for r in results["unfixable"]],
    }

    out_dir = PROJECT / "scratch" / "bundle_regen"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"{level_name}_report.json"
    with open(report_path, "w") as fh:
        json.dump(report, fh, indent=2)

    print(
        f"[{level_name}] Done. passed={report['passed']}, fixed={report['fixed']}, "
        f"unfixable={len(report['unfixable'])}. Report: {report_path}"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", required=True, help="Level name")
    parser.add_argument("--workers", type=int, default=4, help="Worker processes")
    args = parser.parse_args()

    report = validate_and_regen(args.level, args.workers)
    if report["unfixable"]:
        print(
            f"WARNING: {len(report['unfixable'])} seeds could not be fixed: "
            f"{report['unfixable'][:20]}"
        )
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
