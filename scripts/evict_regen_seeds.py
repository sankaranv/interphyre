"""Mark regen seeds as impossible in the production bundle.

Required before running merge_chunks.py for a partial regen: merge_chunks.py only overrides
existing entries when the new result is valid and the existing result is impossible. Fragile
seeds have status='valid', so without eviction the new robust solution would not replace the
fragile one (same status, same or higher variant).

Usage:
    python scripts/evict_regen_seeds.py --level <level> --seeds <regen_seeds.txt>

Writes the evicted bundle in-place to interphyre/data/levels/<level>.json.lzma.
"""

from __future__ import annotations

import argparse
import json
import lzma
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
BUNDLE_DIR = PROJECT / "interphyre" / "data" / "levels"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", required=True)
    parser.add_argument("--seeds", required=True, type=Path, help="File with one seed per line")
    args = parser.parse_args()

    regen_seeds = set()
    with open(args.seeds) as f:
        for line in f:
            line = line.strip()
            if line:
                regen_seeds.add(int(line))

    bundle_path = BUNDLE_DIR / f"{args.level}.json.lzma"
    with lzma.open(bundle_path, "rb") as f:
        data = json.load(f)

    entries = data["entries"]
    evicted = 0
    for entry in entries:
        if entry["seed"] in regen_seeds and entry["status"] == "valid":
            entry["status"] = "impossible"
            entry["scene"] = None
            entry["solution"] = None
            evicted += 1

    with lzma.open(bundle_path, "wb") as f:
        f.write(json.dumps(data).encode())

    valid_after = sum(1 for e in entries if e["status"] == "valid")
    print(f"[{args.level}] evicted {evicted} fragile entries; {valid_after}/{len(entries)} valid remain")


if __name__ == "__main__":
    main()
