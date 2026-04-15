#!/usr/bin/env python3
"""Collect all per-level validate_and_regen reports and print a summary table.

Reads scratch/bundle_regen/<level>_report.json for all 25 levels and prints:
  - Per-level counts: total_valid, passed, fixed, unfixable
  - Grand total and any levels still needing attention

Exit 0 if all levels are 100% (passed + fixed == total_valid, unfixable == 0).
Exit 1 if any level has unfixable seeds.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).parent.parent
REPORT_DIR = PROJECT / "scratch" / "bundle_regen"

LEVELS = [
    "basket_case", "catapult", "cliffhanger", "dive_bomb", "down_to_earth",
    "end_of_line", "falling_into_place", "flagpole_sitta", "just_a_nudge",
    "keyhole", "locust_swarm", "marble_race", "mind_the_gap", "off_the_rails",
    "pass_the_parcel", "pinball_machine", "seesaw", "staircase", "straight_face",
    "the_cradle", "the_funnel", "tipping_point", "two_body_problem",
    "wedge_issue", "zebra_crossing",
]


def main() -> None:
    col = max(len(n) for n in LEVELS)
    header = f"{'Level':<{col}}  {'total':>7}  {'passed':>7}  {'fixed':>7}  {'unfixable':>9}"
    print(header)
    print("-" * len(header))

    total_valid = total_passed = total_fixed = 0
    all_unfixable: list[str] = []
    missing: list[str] = []

    for level in LEVELS:
        report_path = REPORT_DIR / f"{level}_report.json"
        if not report_path.exists():
            missing.append(level)
            print(f"{level:<{col}}  {'MISSING':>7}")
            continue

        with open(report_path) as fh:
            r = json.load(fh)

        total_valid += r["total_valid"]
        total_passed += r["passed"]
        total_fixed += r["fixed"]
        unfixable_count = len(r["unfixable"])
        if unfixable_count:
            all_unfixable.append(f"{level} ({unfixable_count})")

        flag = " !" if unfixable_count else ""
        print(
            f"{level:<{col}}  {r['total_valid']:>7}  {r['passed']:>7}  "
            f"{r['fixed']:>7}  {unfixable_count:>9}{flag}"
        )

    print("-" * len(header))
    print(
        f"{'TOTAL':<{col}}  {total_valid:>7}  {total_passed:>7}  "
        f"{total_fixed:>7}  {len(all_unfixable):>9}"
    )

    if missing:
        print(f"\nMissing reports: {', '.join(missing)}")
        sys.exit(1)

    if all_unfixable:
        print(f"\nLevels with unfixable seeds: {', '.join(all_unfixable)}")
        sys.exit(1)

    print("\nAll levels: 0 unfixable. Bundle is ready for final validation.")
    sys.exit(0)


if __name__ == "__main__":
    main()
