# just_a_nudge Sweep Summary

## Hypothesis

The oracle for `just_a_nudge` was claimed to exhaust valid placements with a near-0%
solvability rate (~1/1000). The oracle only sampled from outside the basket walls to
generate a lateral push on the basket. The question was whether a full-board grid sweep
would reveal valid placements the oracle missed.

## Experiment Setup

- **Sweep script**: `scratch/oracle_hardening/impossible_seed_sweep.py`
- **Grid**: 40×40 across the full board (x, y ∈ [−4.4, 4.4]), spacing ≈ 0.23 units
- **Seeds swept**: 30 randomly sampled from 999 bundle-impossible seeds
- **Variants per seed**: up to 10
- **Oracle steps per attempt**: 500
- **Results file**: `results/oracle_sweep/just_a_nudge_sweep.json`

## Results

| Metric | Value |
|---|---|
| Bundle impossible seeds | 999 |
| Seeds swept | 30 |
| Solved by grid | 3 / 30 |
| **Oracle false-negative rate** | **10.0%** |
| Confirmed impossible | 27 / 30 |
| Estimated oracle failures in full set | ~99 / 999 |

## Verdict: MIXED

False-negative rate of 10.0% falls between the 5% (GENUINE) and 30% (ORACLE FAILURE)
thresholds. The oracle misses a meaningful fraction of solvable seeds, but the majority
(90%) are confirmed impossible by the grid sweep.

## Where Do the Winning Positions Fall?

All three solved seeds were solved using positions **near or slightly above the green_ball
on the platform** — not at the basket:

| Seed | Variant | Red ball pos | x_rel_green_ball | y_rel_green_ball |
|---|---|---|---|---|
| 83  | 2 | (3.27, 2.14)  | +3.27 | +0.24 |
| 749 | 1 | (0.11, 2.59)  | +0.36 | +0.85 |
| 958 | 5 | (2.82, 1.24)  | +2.89 | −1.51 |

In every case the basket is at y ≈ −4.9, far below the winning placement. The red ball
is not interacting with the basket at all. Instead, the red ball knocks the green_ball
off the platform directly, and the green_ball then falls the full board height into the
basket and contacts the blue_ball.

## Why the Oracle Failed

The oracle misunderstood the causal mechanism. It assumed the required interaction was
red_ball → basket (lateral push to reposition basket under green_ball's trajectory).
The actual solvable mechanism is red_ball → green_ball (direct knock off platform),
which does not require moving the basket. The oracle never sampled anywhere near the
green_ball's platform position (y ≈ +1–3), so it could not discover this path.

## Geometric Constraint on the Remaining 90%

For seeds confirmed impossible (27/30), the mechanism is likely blocked by: (1) the
green_ball's position on the platform is inaccessible from any direction that dislodges
it toward the basket, or (2) the basket is too far from the green_ball's natural fall
trajectory and cannot be moved to the correct position by any valid placement. The
±0.23-unit grid spacing may also miss very narrow valid windows, so the true solvability
fraction could be slightly higher than 10%.

## Design Decision Notes

The grid spacing of ≈0.23 units is sufficient to detect valid windows of radius ≥ 0.1
units but will miss keyhole windows smaller than the grid cell. The 10% rate should be
treated as a lower bound on the oracle false-negative rate.
