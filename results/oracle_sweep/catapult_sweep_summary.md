# catapult sweep study

**Date:** 2026-04-03  
**Seeds swept:** 50 of 806 impossible  
**Grid:** 40×40 (spacing ≈ 0.23 units), variants: 10, oracle_steps: 500

## Hypothesis

The catapult oracle's narrow placement band (y ∈ [arm_top + radius + 0.01, arm_top + radius + 0.3],
a 0.29-unit window directly above the right arm tip) represents the same narrow-range pattern
that produced 100% false-negative rates in dive_bomb, mind_the_gap, and the_funnel. The oracle
docstring claim that "~84% appear genuinely impossible" was validated only against the same
narrow oracle, not a full-board sweep. Expected: >30% false-negative rate, oracle redesign required.

## Setup

All 806 seeds from `catapult.json.lzma` with no `valid` variant were loaded. A random sample
of 50 seeds (rng_seed=42) was swept with a 40×40 full-board grid spanning x, y ∈ [−4.4, 4.4].
For each seed, all 10 variants were tried; the sweep stopped at the first (variant, position)
pair that resolved the level in 500 physics steps. Results were written to `catapult_sweep.json`.

Oracle zone classification used the published oracle bounds:
- **x zone**: `[arm_right − 1.5, arm_right]` = `[−2.30, −0.80]` (arm_right is fixed at −0.80)
- **y zone**: `[arm_top + radius + 0.01, arm_top + radius + 0.30]` (0.29-unit band above arm)

## Result

**30 / 50 swept seeds were solved by the grid (60.0% oracle false-negative rate).**  
Estimated oracle failures across the full impossible set: ~483 / 806.

### Zone classification of 30 winning positions

| Zone | Count | Fraction |
|------|-------|---------|
| Inside oracle zone | 0 | 0% |
| Outside oracle zone | 30 | 100% |

**Every single winning position is outside the oracle's narrow band.** The oracle's causal
model — that a ball dropped from within 0.01–0.30 units above the right arm tip adds torque
— is not the mechanism these seeds use. Zero of 30 solved seeds produced a winning placement
within the oracle's sampling region.

### Where do winning positions cluster?

Winning positions are distributed broadly across the board, not clustered near the arm tip:

| Region | Count | Fraction |
|--------|-------|---------|
| Left side (x < −1.5, y > 2.5) | 16 | 53% |
| Right side (x > 1.5) | 6 | 20% |
| Mid-board | 8 | 27% |

**y distribution:**
- All 30 winning positions have y > −2 (all well above the bottom of the board)
- 27/30 (90%) have y > 0 (upper half of the board)
- 23/30 (77%) have y > 2

**Distance above arm_top (y_rel = win_y − arm_top):**
- Oracle y_rel range (with radius=0.5): 0.51 to 0.80 units
- Actual y_rel range: 0.65 to 6.78 units (median 5.08 units)

The oracle's narrow band sits at the very bottom of the actual valid range. At y_rel ≈ 0.65,
only one seed was solved (seed=667); the vast majority of solvable seeds require placements
**5–7 units above the arm surface**. The valid mechanism is not "drop from just above the arm"
but rather "drop from high up and let the ball land on or near the arm with sufficient momentum
to trigger the catapult."

### Confirmed impossible seeds — geometry

20/50 seeds were not solved by the grid sweep. Their arm_top values span the full range of
solved seeds (min=−2.97, max=+0.39, median=−2.30 vs. solved: min=−3.10, max=+0.59,
median=−2.31), confirming that arm height does not distinguish solvable from impossible seeds.
These 20 seeds are likely genuinely impossible due to basket/ledge geometry that prevents the
green ball from entering the basket regardless of where the red ball lands. The grid sweep is
a lower bound; some may be solvable with placements finer than the 0.23-unit grid spacing.

## Verdict

**ORACLE FAILURE** — 60% false-negative rate in the sampled set. The oracle's docstring
claim of "~84% genuine impossibility" is false: in the sweep, 60% of labeled-impossible
seeds are solvable by full-board grid search.

The failure has one root cause:

**Wrong causal model.** The oracle assumes the valid mechanism is a low-energy drop from
just above the right arm (y_rel ≤ 0.30 + radius). In practice, the winning mechanism
involves high placements (y_rel median 5.08 units) that drop from far above the arm or from
elsewhere on the board. 0/30 winning positions fell within the oracle's sampling region.

The oracle's x-range restriction (arm_right − 1.5 to arm_right) further compounds the error:
26% of winning positions have x > arm_right (entirely outside the oracle's x range), and 53%
are far to the left at x < −1.5.

## Design recommendation

The oracle must be redesigned around the empirically correct causal model. Key constraints
from the sweep:

1. **Y range must be high above the arm**, not just above the surface. A zone spanning
   y ∈ [arm_top + 1.0, MAX_Y − radius] covers the bulk of observed winning positions.
2. **X range must be wide.** Winning positions span x ∈ [−4.4, +4.4]. The oracle should
   sample the broad left region (x < arm_right) and also allow right-side placements.
3. **A proposed replacement oracle** with two zones would cover the observed distribution:
   - **Zone A** (high above arm, left of arm): `x ∈ [MIN_X, arm_right + 1.0]`,
     `y ∈ [arm_top + 1.0, MAX_Y − radius]` — covers the 16 top-left wins and mid-board wins
   - **Zone B** (right side, broad): `x ∈ [arm_right, MAX_X − radius]`,
     `y ∈ [0, MAX_Y − radius]` — covers the 6 right-side wins

After redesigning the oracle, re-run bundle generation for catapult and verify the
impossible count falls substantially. Estimated impact: ~483 of 806 current impossible seeds
are oracle false negatives that should be reclassified as `valid` or `hard`.
