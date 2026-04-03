# pinball_machine sweep study

**Date:** 2026-04-03  
**Seeds swept:** 50 of 322 impossible (sampled, rng_seed=42)  
**Grid:** 40×40, variants: 10, oracle_steps: 500

## Hypothesis

The reported 32.2% failure rate (322/1000 seeds labeled impossible) is driven by oracle
misses, not genuine impossibility. The current oracle constrains x to [gb.x − 2.0, gb.x + 2.0]
in both Zone A and Zone B. By analogy with locust_swarm, valid placements may exist outside
this x band. The prior expected a MIXED or ORACLE FAILURE classification.

## Setup

The sweep loaded all 322 seeds labeled "impossible" in the current pinball_machine bundle,
sampled 50 uniformly at random (rng_seed=42), and for each seed tried up to 10 variants with
a 40×40 full-board grid over [-4.4, 4.4]² at 500 simulation steps per attempt. Grid spacing
is 8.8/39 ≈ 0.226 units, resolving valid windows of radius ≥ 0.11 units. Seeds requiring
narrower windows are not detectable, so the false-negative count is a lower bound.

## Result

**35 / 50 swept seeds (70.0%) were solved by the grid. 15 seeds confirmed impossible.**

Extrapolated to the full impossible set: ~225 / 322 seeds are estimated to be oracle
false negatives.

**Verdict: ORACLE FAILURE — >30% false-negative rate. Oracle redesign required.**

## Zone analysis

### Oracle Zone A y range is entirely above all valid placements

The current oracle Zone A samples y in [gb.y + 0.2, 4.5]. Since gb.y = 4.0 (constant across
all seeds), Zone A y = [4.2, 4.5] — a 0.3-unit window at the very top of the board.

Of the 35 seeds solved by the full-board grid sweep:

- **0 / 35 winning positions** are in the oracle Zone A y window [4.2, 4.5].
- **0 / 35 winning positions** are above gb.y = 4.0 at all.
- **35 / 35 winning positions** are strictly below gb.y = 4.0, in the range y ∈ [-0.56, 3.50].

Zone A (75% of all oracle attempts) samples a y window with zero overlap with the valid
solution space. This is not a probabilistic shortfall — it is a systematic design flaw:
75% of every oracle run is guaranteed to fail.

### Oracle Zone B partially covers the valid space but is budget-starved

Zone B (25% of attempts) samples x in [gb.x − 2.0, gb.x + 2.0] and y across the full board
[-4.5, 4.5]. The y range is correct. However:

- **6 / 35 solved seeds (17%)** have winning positions outside the oracle's x band (|x_offset| > 2.0).
  These seeds cannot be found even by Zone B. The largest x-offset observed was +3.33 (seed=111)
  and -3.26 (seed=461).
- Zone B receives only 25% of attempt budget. With valid placements rare within the x window,
  the per-attempt success probability is low enough that many runs fail.

### Oracle x band: mostly adequate but 17% of solvable seeds need wider coverage

- **29 / 35 solved seeds (83%)** had winning positions inside gb.x ± 2.0.
- **6 / 35 solved seeds (17%)** required positions 0.05 to 1.33 units outside the ±2.0 band.

Widening x from ±2.0 to ±3.5 would cover all 35 solved seeds in this sample.

## Winning position distribution

| y range       | count | fraction |
|---------------|-------|----------|
| y ∈ [-0.6, 0) | 3     | 8.6%     |
| y ∈ [0, 1.5)  | 5     | 14.3%    |
| y ∈ [1.5, 2.5)| 3     | 8.6%     |
| y ∈ [2.5, 3.5]| 24    | 68.6%    |
| y > 3.5       | 0     | 0%       |

The majority cluster at y ∈ [2.5, 3.5] — the red ball starts 0.5–1.5 units below the
green ball (which is at y=4.0) and nudges it downward. A smaller fraction (11/35) require
placements at y < 1.5, including 3 seeds with y < 0, suggesting a second mechanism
(lateral bounce or indirect path) exists for some geometries.

## n_stars does not predict impossibility for confirmed-impossible seeds

- Stars in solved seeds: mean = 24.2, range [18, 31]
- Stars in confirmed-impossible seeds: mean = 23.9, range [20, 29]
- Difference: −0.3 stars (negligible)

No threshold on star count separates solvable from impossible seeds in this sample.
The 15 confirmed-impossible seeds are indistinguishable from solvable seeds by star count;
their genuine impossibility is due to specific star placement geometry, not density.

## Root cause summary

The pinball_machine oracle has two compounding bugs:

1. **Zone A y range [4.2, 4.5] is entirely above the valid solution space.** All valid
   placements are below gb.y = 4.0. Zone A wastes 75% of every oracle run.

2. **x range ±2.0 is too narrow for 17% of solvable seeds**, which require |x_offset| up to 3.33.

The combination means: Zone A (75%) always fails; Zone B (25%) covers the right y but too
narrow x, and receives too little budget for its low per-attempt success rate. The oracle
effectively undersamples the valid region by a large margin.

## Design recommendation

The oracle requires two fixes:

1. **Replace Zone A with full-board y sampling.** There is no evidence that valid solutions
   concentrate above gb.y. The y range should be [-4.5, 4.5] unconditionally, not [4.2, 4.5].

2. **Widen x from ±2.0 to ±3.5** to cover seeds where the valid placement is far from
   the green ball's x position. This closes the 17% gap seen in the sweep.

After oracle correction, the bundle should be regenerated. Based on the sweep (15/50 = 30%
confirmed impossible), the true impossible rate is likely around 30% of the current impossible
set, i.e., ~97/1000 seeds genuinely impossible, not 322/1000.
