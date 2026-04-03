# locust_swarm sweep study

**Date:** 2026-04-03  
**Seeds swept:** 50 of 496 impossible (sampled, rng_seed=42)  
**Grid:** 40×40, variants: 10, oracle_steps: 500

## Hypothesis

The oracle uses a fixed x range of gb.x ± 2.5 for both Zone A (75%, y ∈ [gb.y+0.2, gb.y+2.0])
and Zone B (25%, full-board y). If valid placements exist at x values far from the green_ball,
the oracle's x-pinning would produce false negatives. Additionally, Zone A's y window
[gb.y+0.2, gb.y+2.0] may be misaligned given gb.y is constant at 4.0, placing the entire Zone A
at y ∈ [4.2, 4.5] — a 0.3-unit sliver at the top of the board. The prior expected a
mixed-to-oracle-failure classification.

## Setup

The sweep loaded 496 seeds labeled "impossible" in the current locust_swarm bundle and sampled
50 uniformly at random. For each seed, up to 10 variants were tested; within each variant a
40×40 grid of (x, y) positions spanning the full board [-4.4, 4.4]² was tried at 500 simulation
steps per attempt. Any grid success classifies the seed as an oracle false negative. The grid
spacing is 8.8/39 ≈ 0.226 units, resolving valid windows of radius ≥ 0.11 units. This count
is therefore a lower bound on the true false-negative rate.

## Result

**32 / 50 swept seeds (64.0%) were solved by the full-board grid sweep.**  
18 / 50 seeds were confirmed impossible (no grid position succeeded across 10 variants).

Extrapolated to the full impossible set: approximately **317 / 496** seeds are oracle false
negatives. These 317 seeds are solvable but labeled impossible, inflating the failure rate
from a true ~36% to the reported 49.6%.

### Winning position geometry

All 32 solved seeds have gb.y = 4.0 (green_ball is always at the top of the board).

**Zero of 32 solutions fall in Zone A's y range [4.2, 4.5].** The nearest solution is seed 347
at y = 4.17, which is still below 4.2. The entire valid y range for locust_swarm is
y ∈ [0.79, 4.17] (mean = 2.32), concentrated in the mid-board band y ∈ [1.5, 3.0] (27/32 = 84%).

This means Zone A (75% of oracle attempts) is directed at a y-window that contains zero valid
placements. Only Zone B's 25% of attempts sample the correct y range, so the oracle's effective
search capacity for this level is 25% of its stated n_attempts.

**14 / 32 solved seeds (44%) have winning x OUTSIDE the oracle's x range gb.x ± 2.5.**  
x offsets for the 14 out-of-range solutions range from −5.89 to +5.39 board units, with a mean
absolute offset of 4.0 units beyond the ±2.5 cutoff. This is not a narrow-miss effect: these
are placements on the opposite side of the board from the green_ball.

Distribution of x offsets (all 32 seeds):
- |offset| ≤ 2.5 (inside oracle x range): 18 seeds
- |offset| > 2.5 (outside oracle x range): 14 seeds
- Maximum |offset|: 5.89 units (seed 108, gb_x=2.85, winning x=−3.05)

Both failure modes are independent contributors. Fixing only the y bug (Zone A → valid y range)
would still miss the 14 seeds with wide x offsets.

### Star count vs impossibility

Mean n_stars for seeds solved by grid: **47.0** (range 34–60)  
Mean n_stars for confirmed-impossible seeds: **45.4** (range 39–56)

The distributions overlap completely. Star count does not predict impossibility at this
sample size. The confirmed-impossible seeds are not distinguished by higher star density;
they appear geometrically blocked regardless of placement.

## Verdict

**ORACLE FAILURE** — 64% false-negative rate, well above the 30% redesign threshold.

Two structural defects compound:

1. **Zone A y-range collapse.** With gb.y = 4.0 constant, Zone A samples y ∈ [4.2, 4.5]
   (0.3 units wide at the board ceiling). No valid solution in this sweep falls in that range.
   75% of oracle attempts are directed at a dead zone.

2. **X-range too narrow.** 44% of solvable seeds have winning placements with |x − gb.x| > 2.5.
   The oracle's fixed x band of gb.x ± 2.5 misses approximately half the valid x domain.

The oracle's docstring claim — "most impossible seeds are genuinely impossible (dense star chains
block all paths)" — was not supported by prior validation. This sweep contradicts it: 64% of
sampled impossible seeds are solvable by the grid. Density of star chains does not predict
impossibility (n_stars is essentially identical between groups).

## Design recommendation

The oracle requires a two-part fix:

1. **Remap Zone A's y target.** The green_ball at y = 4.0 needs the red ball to approach from
   **below**, not above. The correct Zone A y range is approximately [0.5, 3.5] (centered on
   mid-board, below the green_ball), not [4.2, 4.5]. The valid placement cluster is
   y ∈ [1.5, 3.0] in 84% of solved seeds.

2. **Expand x range to full board.** Replace gb.x ± 2.5 with a full-board x range [-4.5, 4.5]
   in both zones, or at minimum expand to ± 4.5. 44% of valid placements require x more than 2.5
   units from the green_ball.

After fixing the oracle, the locust_swarm bundle must be regenerated. The expected outcome is
recovery of most of the ~317 false-negative seeds, reducing the impossible rate from 49.6%
toward the genuine impossible rate of approximately 36% × (18/50) ≈ ~18% (rough estimate; the
confirmed-impossible sample is only 18 seeds across a coarse grid).
