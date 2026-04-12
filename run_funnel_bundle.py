"""Run the_funnel bundle generation in-process without multiprocessing."""
import json
import lzma
import sys
from collections import defaultdict
from pathlib import Path

# Resolve project root relative to this script so it runs on any machine
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from interphyre.validation._bundle import (
    _assert_round_trip,
    _git_short_hash,
    _validate_seed,
)
from interphyre.validation.registry import _compute_schema_hash

_SCENES_DIR = _PROJECT_ROOT / "interphyre" / "data" / "scenes"

level_name = "the_funnel"
seeds = range(0, 10000)
max_variants = 10
n_attempts = 200
oracle_steps = 500

print(f"[{level_name}] Validating {len(seeds)} seeds in-process...", flush=True)

all_entries = []
for i, seed in enumerate(seeds):
    try:
        entries = _validate_seed(
            (level_name, seed, max_variants, n_attempts, oracle_steps)
        )
        all_entries.extend(entries)
    except Exception as exc:
        print(f"  FAILED seed={seed}: {exc}", flush=True)
        raise
    if (i + 1) % 500 == 0:
        print(f"  {i + 1}/{len(seeds)} seeds done", flush=True)

valid_entries = [e for e in all_entries if e["status"] == "valid"]
print(
    f"[{level_name}] Verifying round-trip for {len(valid_entries)} valid entries...",
    flush=True,
)
for entry in valid_entries:
    _assert_round_trip(level_name, entry["seed"], entry["variant"], entry["scene"])

schema_hash = _compute_schema_hash(level_name)
all_entries.sort(key=lambda e: (e["seed"], e["variant"]))

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
    f"trivial: {statuses.count('trivial')}, "
    f"impossible: {statuses.count('impossible')} "
    f"→ {bundle_path}",
    flush=True,
)

by_seed: dict = defaultdict(set)
for e in all_entries:
    by_seed[e["seed"]].add(e["status"])
total = len(by_seed)
solvable = sum(1 for s in by_seed.values() if s & {"valid", "trivial"})
print(f"Seeds: {total}, Solvable: {solvable}/{total} ({100*solvable/total:.1f}%)")
status_counts: dict = defaultdict(int)
for e in all_entries:
    status_counts[e["status"]] += 1
print(f"Status: {dict(status_counts)}")
print(f"oracle_commit: {_git_short_hash()}")
