"""Offline bundle generator for interphyre/data/scenes/.

Runs the same validation pipeline as validate_level but writes output to
lzma-compressed JSON files that ship with the package. These files feed the
O(1) bundled lookup tier in SeedRegistry.

Not part of the public API. Must not be imported by runtime code.

Usage (run once at release):
    python -m interphyre.validation._bundle --levels all --seeds 0:1000 --workers 8
"""

from __future__ import annotations

import argparse
import json
import lzma
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from interphyre.config import SimulationConfig
from interphyre.levels import build_level_from_scene, list_levels, load_level
from interphyre.validation import _ORACLE_RNG_SALT
from interphyre.validation.checks import extract_scene_dict, is_trivial
from interphyre.validation.oracles import get_oracle, get_solver
from interphyre.validation.registry import _compute_schema_hash

# Output directory for bundled lzma files.
_SCENES_DIR = Path(__file__).parent.parent / "data" / "scenes"


def _git_short_hash() -> str:
    """Return the short git hash of HEAD at bundle generation time.

    Stored as bundle metadata['oracle_commit'] so future engineers can identify
    which oracle version produced the bundle. Falls back to 'unknown' if git is
    unavailable (e.g., in CI environments without a .git directory).
    """
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).parent,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


_DEFAULT_MAX_VARIANTS = 10
_DEFAULT_N_ATTEMPTS = 50
_DEFAULT_ORACLE_STEPS = 500
_DEFAULT_WORKERS = 4


def _oracle_rng(seed: int, variant: int) -> np.random.Generator:
    """Return a reproducible RNG for the oracle, seeded from (seed, variant, salt).

    Three-integer list seeding matches validate_level in __init__.py, ensuring
    that bundle and live paths produce identical oracle RNG sequences for every
    (seed, variant) pair.
    """
    return np.random.default_rng([seed, variant, _ORACLE_RNG_SALT])


def _validate_seed(args: tuple) -> list[dict]:
    """Validate all variants for one (level_name, seed) pair.

    Top-level function required for ProcessPoolExecutor pickling on macOS (spawn).

    Returns one entry per variant tried. Each entry has {seed, variant, status,
    scene, solution} where scene and solution are None for non-valid entries.
    solution is a list of [x, y, radius] lists (one per action object) when a
    solver is registered, or None when only an oracle bool path is available.
    Stops at the first valid variant — later variants are skipped since only one
    valid geometry per seed is needed for the bundle.
    """
    level_name, seed, max_variants, n_attempts, oracle_steps = args
    config = SimulationConfig()
    level_solver = get_solver(level_name)
    oracle = get_oracle(level_name)
    entries = []

    for variant in range(max_variants):
        level = load_level(level_name, seed=seed, variant=variant)

        # Trivial check: skip variants where the success condition is already met
        # at t=0 without any agent action.  These are not valid training examples
        # (no placement was needed) and must not appear in the bundle.
        if is_trivial(level, config):
            continue

        # Solver path: prefer get_solver so the winning placement is captured.
        # Oracle bool path: fall back when no solver is registered.
        rng = _oracle_rng(seed, variant)
        if level_solver is not None:
            sol = level_solver(level, config, n_attempts, oracle_steps, rng)
            if sol is not None:
                scene_dict = extract_scene_dict(level)
                # Encode each (x, y, radius) tuple as a [x, y, radius] list for
                # JSON serialisability and consistent structure across entries.
                solution_json = [[pos[0], pos[1], pos[2]] for pos in sol]
                entries.append(
                    {
                        "seed": seed,
                        "variant": variant,
                        "status": "valid",
                        "scene": scene_dict,
                        "solution": solution_json,
                    }
                )
                # First valid variant found — stop trying further variants.
                break
            entries.append(
                {
                    "seed": seed,
                    "variant": variant,
                    "status": "impossible",
                    "scene": None,
                    "solution": None,
                }
            )
        else:
            # Oracle-only path: solution is unavailable.
            if oracle(level, config, n_attempts, oracle_steps, rng):
                scene_dict = extract_scene_dict(level)
                entries.append(
                    {
                        "seed": seed,
                        "variant": variant,
                        "status": "valid",
                        "scene": scene_dict,
                        "solution": None,
                    }
                )
                break
            entries.append(
                {
                    "seed": seed,
                    "variant": variant,
                    "status": "impossible",
                    "scene": None,
                    "solution": None,
                }
            )

    return entries


def _assert_round_trip(
    level_name: str, seed: int, variant: int, scene_dict: dict
) -> None:
    """Assert that build_level_from_scene reconstructs the scene bit-identically.

    Aborts with RuntimeError on any mismatch — this is a hard invariant for
    reproducibility. A failure means extract_scene_dict is missing an attribute
    that affects geometry, and the bundle must not be written until fixed.
    """
    reconstructed = build_level_from_scene(level_name, scene_dict)
    scene_dict_2 = extract_scene_dict(reconstructed)

    if scene_dict == scene_dict_2:
        return

    mismatches = [
        f"  {name}.{attr}: {scene_dict[name][attr]!r} != {scene_dict_2.get(name, {}).get(attr)!r}"
        for name in scene_dict
        for attr in scene_dict[name]
        if scene_dict[name][attr] != scene_dict_2.get(name, {}).get(attr)
    ]
    raise RuntimeError(
        f"Round-trip assertion failed for {level_name} seed={seed} variant={variant}.\n"
        f"Mismatched attributes:\n" + "\n".join(mismatches)
    )


def _build_level_bundle(
    level_name: str,
    seeds: range,
    *,
    max_variants: int,
    n_attempts: int,
    oracle_steps: int,
    workers: int,
) -> None:
    """Validate all seeds for one level and write the lzma bundle file."""
    print(f"[{level_name}] Validating {len(seeds)} seeds with {workers} workers...")

    work_items = [
        (level_name, seed, max_variants, n_attempts, oracle_steps) for seed in seeds
    ]

    all_entries: list[dict] = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_validate_seed, item): item[1] for item in work_items}
        completed = 0
        for future in as_completed(futures):
            seed = futures[future]
            try:
                entries = future.result()
            except Exception as exc:
                raise RuntimeError(
                    f"[{level_name}] Worker failed for seed={seed}: {exc}"
                ) from exc
            all_entries.extend(entries)
            completed += 1
            if completed % 100 == 0:
                print(f"[{level_name}]   {completed}/{len(seeds)} seeds done")

    # Round-trip assertion: every valid entry's scene must reconstruct identically.
    valid_entries = [e for e in all_entries if e["status"] == "valid"]
    print(
        f"[{level_name}] Verifying round-trip for {len(valid_entries)} valid entries..."
    )
    for entry in valid_entries:
        _assert_round_trip(level_name, entry["seed"], entry["variant"], entry["scene"])

    # Compute schema hash: SHA-256 of the attribute key structure at seed=0.
    # This hash is checked on load to detect constructor changes that would make
    # stored scenes produce wrong geometry.
    schema_hash = _compute_schema_hash(level_name)

    # Sort entries for deterministic output ordering.
    all_entries.sort(key=lambda e: (e["seed"], e["variant"]))

    # Write lzma-compressed JSON to interphyre/data/scenes/.
    _SCENES_DIR.mkdir(parents=True, exist_ok=True)
    bundle_path = _SCENES_DIR / f"{level_name}.json.lzma"
    with lzma.open(bundle_path, "wt", encoding="utf-8") as fh:
        json.dump(
            {
                "schema_hash": schema_hash,
                "oracle_commit": _git_short_hash(),
                "entries": all_entries,
            },
            fh,
        )

    statuses = [e["status"] for e in all_entries]
    print(
        f"[{level_name}] Done — valid: {statuses.count('valid')}, "
        f"impossible: {statuses.count('impossible')} "
        f"→ {bundle_path}"
    )


def _parse_seeds(seeds_arg: str) -> range:
    """Parse Python slice notation into a range. Accepts start:stop or start:stop:step."""
    parts = seeds_arg.split(":")
    try:
        if len(parts) == 2:
            return range(int(parts[0]), int(parts[1]))
        if len(parts) == 3:
            return range(int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        pass
    raise argparse.ArgumentTypeError(
        f"Invalid seeds format '{seeds_arg}'. Expected start:stop or start:stop:step."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate bundled validation data for interphyre/data/scenes/."
    )
    parser.add_argument(
        "--levels",
        nargs="+",
        default=["all"],
        help="Level names to bundle, or 'all' for every registered level.",
    )
    parser.add_argument(
        "--seeds",
        default="0:1000",
        help="Seed range in slice notation: start:stop or start:stop:step.",
    )
    parser.add_argument("--workers", type=int, default=_DEFAULT_WORKERS)
    parser.add_argument("--max-variants", type=int, default=_DEFAULT_MAX_VARIANTS)
    parser.add_argument("--attempts", type=int, default=_DEFAULT_N_ATTEMPTS)
    parser.add_argument("--oracle-steps", type=int, default=_DEFAULT_ORACLE_STEPS)

    args = parser.parse_args()

    seeds = _parse_seeds(args.seeds)
    level_names = list_levels() if args.levels == ["all"] else args.levels

    print(
        f"Building bundles: {len(level_names)} levels, "
        f"seeds {args.seeds}, workers={args.workers}"
    )

    for level_name in sorted(level_names):
        _build_level_bundle(
            level_name,
            seeds,
            max_variants=args.max_variants,
            n_attempts=args.attempts,
            oracle_steps=args.oracle_steps,
            workers=args.workers,
        )

    print("All bundles complete.")


if __name__ == "__main__":
    main()
