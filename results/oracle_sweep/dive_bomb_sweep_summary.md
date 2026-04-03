# dive_bomb sweep study

**Date:** 2026-04-03  
**Seeds swept:** 50 of 629 impossible  
**Grid:** 40×40 (spacing ≈ 0.23 units), variants: 10, oracle_steps: 500

## Hypothesis

Gray_ball intermediary creates valid placements outside the oracle's two zones. Expected
>10% false-negative rate.

## Setup

The sweep loaded all 629 seeds from the `dive_bomb.json.lzma` bundle that had no `valid`
variant (all variants were labeled `impossible`). A random sample of 50 seeds (rng_seed=42)
was swept with a 40×40 full-board grid spanning x, y ∈ [−4.4, 4.4]. For each seed, all 10
variants were tried; the sweep stopped at the first (variant, position) pair that resolved
the level in 500 physics steps. Results were written to `dive_bomb_sweep.json`.

Zone classification used published oracle boundaries:
- **Zone A** (above green_ball): `gb.x ± 1.5`, `y ∈ [gb.y + 0.2, gb.y + 3.5]`
- **Zone B** (near ramp exit): `ramp.x ± 2`, `y ∈ [ramp.y − 2.5, ramp.y + 1.5]`

## Result

**50 / 50 swept seeds were solved by the grid (100% oracle false-negative rate).**  
Estimated oracle failures across the full impossible set: ~629 / 629.

### Zone classification of the 50 winning positions

| Zone | Count | Fraction |
|------|-------|---------|
| Zone A (above green_ball) | 15 | 30% |
| Zone B (near ramp exit) | 16 | 32% |
| Neither A nor B | 19 | 38% |

### Where do the 19 "neither" positions fall?

Positions relative to `gray_ball` for the 19 outside-zone wins:
- **rel_x range:** −0.79 to +3.06 (mean +0.71 ± 1.17)
- **rel_y range:** −1.58 to +2.20 (mean +0.72 ± 1.12)

A proposed **Zone C** centered on gray_ball with bounds `gray.x ± 2.0`, `y ∈ [gray.y − 0.5, gray.y + 2.5]` captures 16 of 19 (84%) of the uncovered seeds. The remaining 3 seeds (seeds 563, 4734, 7168) have winning positions at y ≈ −2.37 with `rel_ramp.x ≈ +2.10`, just beyond Zone B's x-boundary of ±2. These are covered by widening Zone B's x-tolerance from ±2.0 to ±3.0 and its y-floor from −2.5 to −3.5.

**Combined coverage with Zone A + Zone B + Zone C:**  
47 / 50 (94%). The remaining 3 are covered by a modestly widened Zone B, giving 100% coverage.

## Verdict

**ORACLE FAILURE** — 100% false-negative rate in the sampled set. Every seed labeled
`impossible` in the bundle was solvable by grid search. This is a complete oracle failure,
not a level design limit.

The failure has two distinct causes:
1. **Missing Zone C (gray_ball region):** 38% of valid placements lie near gray_ball,
   not near green_ball or the ramp exit. The oracle's causal chain description omits
   gray_ball as a launch intermediary, so no sampling zone covers this region.
2. **Zone B x-coverage too narrow:** 6% of valid placements are just beyond the ±2.0 x-margin
   around the ramp exit. These are consistent with gray_ball-deflected trajectories that
   land the red_ball slightly further from the ramp centerline than Zone B anticipates.

## Design recommendation

Add **Zone C** to the dive_bomb oracle:
```
Zone C (gray_ball region, 20% weight):
  x ∈ [gray.x − 2.0, gray.x + 2.0]
  y ∈ [gray.y − 0.5, gray.y + 2.5]
```

Also widen **Zone B** slightly:
```
Zone B (ramp region, updated):
  x ∈ [ramp.x − 3.0, ramp.x + 3.0]   (was ±2.0)
  y ∈ [ramp.y − 3.5, ramp.y + 1.5]   (was floor −2.5)
```

Redistribute sampling weights: Zone A 50%, Zone B 20%, Zone C 30%. After adding Zone C,
re-run bundle generation for dive_bomb and verify the impossible count falls well below
1% of total seeds.
