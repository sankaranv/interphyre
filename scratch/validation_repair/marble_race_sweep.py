"""Empirical sweep of x positions on left_beam for marble_race.

Tests a fine grid of x values (spanning the beam and slightly beyond) across
multiple seeds to find which x range reliably tips the beam clockwise and allows
green_ball to pass. Results guide the oracle redesign.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np

from interphyre.config import SimulationConfig
from interphyre.levels import load_level
from interphyre.validation.oracles import _run_attempt

SEEDS = list(range(20))
N_X_BINS = 30  # grid points across the scan range
N_Y = 3        # y values to test (low, mid, high drop)
ORACLE_STEPS = 500
CONFIG = SimulationConfig()


def scan_seed(seed: int) -> dict:
    level = load_level("marble_race", seed=seed)
    left_beam = level.objects["left_beam"]
    red_ball = level.objects["red_ball"]

    bx = left_beam.x
    bl = left_beam.left
    br = left_beam.right
    by = left_beam.y
    r = red_ball.radius

    # Sweep from 0.2 units left of beam centre to 0.5 units past right edge.
    x_scan_min = bx
    x_scan_max = br + 0.5

    x_values = np.linspace(x_scan_min, x_scan_max, N_X_BINS)
    y_low = by + 0.2
    y_mid = by + 0.8
    y_high = by + 1.5

    hits: dict[tuple[float, float], bool] = {}
    for x in x_values:
        for y in [y_low, y_mid, y_high]:
            success = _run_attempt(level, CONFIG, [(float(x), float(y), r)], ORACLE_STEPS)
            hits[(round(x, 3), round(y, 3))] = success

    # Relative x positions that had any success.
    successful_x = sorted({x for (x, y), v in hits.items() if v})
    rel_x = [round(x - bx, 3) for x in successful_x]

    return {
        "seed": seed,
        "beam_x": round(bx, 3),
        "beam_left": round(bl, 3),
        "beam_right": round(br, 3),
        "beam_length": round(left_beam.length, 3),
        "red_ball_radius": round(r, 3),
        "black_ball_1_x": round(level.objects["black_ball_1"].x, 3),
        "black_ball_2_x": round(level.objects["black_ball_2"].x, 3),
        "successful_x_abs": successful_x,
        "successful_x_rel_to_center": rel_x,
        "n_hits": sum(1 for v in hits.values() if v),
        "n_tested": len(hits),
    }


def main():
    print("=== marble_race beam sweep ===\n")
    print(f"Scanning {N_X_BINS} x positions × {N_Y} y heights for seeds 0-{max(SEEDS)}\n")

    all_results = []
    for seed in SEEDS:
        r = scan_seed(seed)
        all_results.append(r)
        pct = 100.0 * r["n_hits"] / r["n_tested"]
        print(
            f"seed={seed:2d}  beam=[{r['beam_left']:+.2f}, {r['beam_right']:+.2f}]  "
            f"pivot_L={r['black_ball_2_x']:+.2f}  support_R={r['black_ball_1_x']:+.2f}  "
            f"hits={r['n_hits']}/{r['n_tested']} ({pct:.0f}%)  "
            f"success_x_rel={r['successful_x_rel_to_center']}"
        )

    # Aggregate: what fraction of the beam's length is "effective"?
    print("\n=== Summary: relative x positions that tip beam (rel to center) ===")
    all_success_x_rel = []
    for r in all_results:
        all_success_x_rel.extend(r["successful_x_rel_to_center"])

    if all_success_x_rel:
        arr = np.array(all_success_x_rel)
        print(f"  Range of successful x (rel to center): [{arr.min():.3f}, {arr.max():.3f}]")
        print(f"  As fraction of half-length (left_beam.length/2):")
        # Half-lengths vary per seed; show fraction for each seed
        for r in all_results:
            half = r["beam_length"] / 2
            succ_abs = r["successful_x_abs"]
            if succ_abs:
                fracs = [(x - r["beam_x"]) / half for x in succ_abs]
                print(f"    seed={r['seed']:2d}: fracs=[{min(fracs):.2f}, {max(fracs):.2f}]  "
                      f"(half_len={half:.2f})")
    else:
        print("  No successful placements found!")

    print("\n=== Beam geometry summary ===")
    lengths = [r["beam_length"] for r in all_results]
    print(f"  beam_length: min={min(lengths):.2f}  max={max(lengths):.2f}  mean={np.mean(lengths):.2f}")


if __name__ == "__main__":
    main()
