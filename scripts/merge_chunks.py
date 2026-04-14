"""Merge pre-computed bundle chunk files into a production bundle.

Usage:
    python scripts/merge_chunks.py --level <level> --chunks <chunk1.json.lzma> [<chunk2.json.lzma> ...]

Each chunk file is a full bundle JSON (same schema as the production bundle) covering
a subset of seeds. This script merges all chunk entries into the production bundle at
interphyre/data/levels/<level>.json.lzma, preferring valid over impossible for any
seed that appears in multiple sources.
"""

from __future__ import annotations

import argparse
import json
import lzma
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
BUNDLE_DIR = PROJECT / "interphyre" / "data" / "levels"


def read_bundle(path: Path) -> dict:
    with lzma.open(path, "rb") as f:
        return json.load(f)


def write_bundle(path: Path, data: dict) -> None:
    with lzma.open(path, "wb") as f:
        f.write(json.dumps(data).encode())


def merge(level: str, chunk_paths: list[Path]) -> None:
    prod_path = BUNDLE_DIR / f"{level}.json.lzma"

    # Load production bundle (must exist)
    if not prod_path.exists():
        print(f"ERROR: production bundle not found: {prod_path}", file=sys.stderr)
        sys.exit(1)

    prod = read_bundle(prod_path)
    schema_hash = prod.get("schema_hash", "")
    oracle_commit = prod.get("oracle_commit", "")

    # Build seed -> best_entry map from existing production bundle.
    # "best" = prefer valid over impossible; among same status keep lower variant.
    seed_map: dict[int, dict] = {}
    for entry in prod["entries"]:
        seed = entry["seed"]
        existing = seed_map.get(seed)
        if existing is None:
            seed_map[seed] = entry
        elif entry["status"] == "valid" and existing["status"] != "valid":
            seed_map[seed] = entry
        elif entry["status"] == existing["status"] and entry.get("variant", 999) < existing.get("variant", 999):
            seed_map[seed] = entry

    # Merge each chunk into the map
    for chunk_path in chunk_paths:
        if not chunk_path.exists():
            print(f"ERROR: chunk file not found: {chunk_path}", file=sys.stderr)
            sys.exit(1)
        print(f"  Loading chunk: {chunk_path}")
        chunk = read_bundle(chunk_path)
        for entry in chunk["entries"]:
            seed = entry["seed"]
            existing = seed_map.get(seed)
            if existing is None:
                seed_map[seed] = entry
            elif entry["status"] == "valid" and existing["status"] != "valid":
                seed_map[seed] = entry
            elif entry["status"] == existing["status"] and entry.get("variant", 999) < existing.get("variant", 999):
                seed_map[seed] = entry

    # Sort by seed
    all_entries = sorted(seed_map.values(), key=lambda e: e["seed"])

    # Write merged bundle
    merged = {
        "schema_hash": schema_hash,
        "oracle_commit": oracle_commit,
        "entries": all_entries,
    }
    write_bundle(prod_path, merged)

    # Summary
    seeds = set(e["seed"] for e in all_entries)
    valid_seeds = {e["seed"] for e in all_entries if e["status"] == "valid"}
    impossible_seeds = seeds - valid_seeds
    valid = [e for e in all_entries if e["status"] == "valid"]
    variants = [e["variant"] for e in valid]
    avg_var = sum(variants) / len(variants) if variants else float("nan")
    pct_v0 = 100.0 * sum(1 for v in variants if v == 0) / len(variants) if variants else 0.0
    p_eff = 1.0 / (1.0 + avg_var) if avg_var == avg_var else float("nan")

    print(f"\n{level} merged bundle:")
    print(f"  seeds: {len(seeds)}, valid: {len(valid_seeds)}, impossible: {len(impossible_seeds)}")
    print(f"  avg_var: {avg_var:.3f}, pct_v0: {pct_v0:.1f}%, p_eff: {p_eff:.3f}")
    if impossible_seeds:
        print(f"  WARNING: {len(impossible_seeds)} impossible seeds: {sorted(impossible_seeds)[:20]}")
        sys.exit(1)
    if len(seeds) < 10001:
        print(f"  WARN: only {len(seeds)} seeds — expected 10001")
    print("  OK")


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge bundle chunk files into production bundle.")
    parser.add_argument("--level", required=True, help="Level name (e.g. pinball_machine)")
    parser.add_argument("--chunks", nargs="+", required=True, type=Path, help="Chunk .json.lzma files to merge")
    args = parser.parse_args()
    print(f"Merging {len(args.chunks)} chunks into {args.level}...")
    merge(args.level, args.chunks)


if __name__ == "__main__":
    main()
