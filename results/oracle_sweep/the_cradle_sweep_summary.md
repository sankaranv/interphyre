# the_cradle sweep study

**Date:** 2026-04-03
**Seeds swept:** 30 of 1000 impossible (100%)
**Grid:** 40×40, variants: 10, oracle_steps: 500

## Hypothesis

The prior oracle only tried a near-tangent lateral approach beside the green_ball.
A full-board sweep may reveal that top-down impact (red ball dropped from above
the cradle) is the valid mechanism. Expected ORACLE FAILURE classification.

## Setup

All 1000 seeds in the current the_cradle bundle are labeled impossible. A sample
of 30 seeds (rng_seed=42) was swept with a 40×40 full-board grid over [-4.4, 4.4]²
at 500 simulation steps per attempt, across up to 10 variants. Grid spacing ≈ 0.226
units; valid windows of radius ≥ 0.11 units are detectable.

## Result

**25 / 30 swept seeds (83.3%) were solved by the grid. 5 seeds confirmed impossible
(at 40×40 resolution).**

Extrapolated to the full impossible set: approximately **833 / 1000** seeds are
oracle false negatives.

## Verdict

**ORACLE FAILURE** — 83.3% false-negative rate, far above the 30% redesign threshold.

## Root cause: wrong mechanism modeled

The prior oracle tried only lateral placement beside the green_ball
(x_offset ∈ [0.7, 0.99] × sum_r, y at tangent height). This approach was
empirically exhausted with zero success across seeds 0–4 in a prior dense scan.

The full-board sweep reveals the actual valid mechanism: **top-down drop from
above the cradle**. All 25 solved seeds have winning positions at
y ∈ [2.59, 4.40] — well above the green_ball, which sits in the V-cradle at
y ∈ [-3, 0] depending on the seed. The red ball drops from high on the board,
impacts the holder bars or directly hits the green_ball from above, and
dislodges it from the V so it falls to the purple_floor.

### Winning position geometry (25 solved seeds)

- y range: [2.59, 4.40] — **all solutions** in the top 60% of board height
- x range: [-2.37, 3.50] — spread broadly across the board
- Mean position: (x ≈ -0.1, y ≈ 3.8)
- No solutions at y < 2.5; the lateral approach zone (y ≈ green_ball.y) is empty

### Confirmed-impossible seeds (5 seeds)

Seeds 86, 181, 641, 777, 821 were not solved at 40×40 grid resolution.
At 0.226-unit grid spacing, windows narrower than ~0.1 units are not detectable.
These seeds may be genuine design limits or further oracle misses at finer resolution.
The 40×40 grid is a lower bound on solvability.

## Design recommendation

**Replace the lateral-only oracle with a top-down drop oracle.**

Zone A (75% of attempts): x ∈ [gb.x − 3.0, gb.x + 3.0], y ∈ [2.5, 4.5].
  Covers the empirical solution cluster (all 25 sweep solutions fall here).

Zone B (25% of attempts): full-board x and y [-4.5, 4.5].
  Fallback for seeds with edge-case geometry.

The oracle also requires a solver function (not just oracle bool) to record
solutions for bundle generation.

After oracle fix, regenerate the bundle. Expected outcome: most of the ~833
false-negative seeds are recovered, reducing the impossible rate from 100%
toward the genuine impossible rate of ~17% (5/30 in this sweep, rough estimate).
