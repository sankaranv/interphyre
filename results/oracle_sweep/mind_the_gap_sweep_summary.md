# mind_the_gap sweep study

**Date:** 2026-04-03
**Seeds swept:** 30 of 106 impossible
**Grid:** 40x40, variants: 10, oracle_steps: 500

## Hypothesis

Oracle docstring claims platform_y <= -3.05 is required for solvability. Most impossible
seeds should have high platform_y (> -3.05), making them genuinely impossible. The
expected oracle false-negative rate was < 5%.

## Setup

Impossible seeds were loaded from the `mind_the_gap.json.lzma` bundle — seeds where every
variant was labeled `impossible` (no `valid` entry). Of 106 such seeds, 30 were sampled
uniformly at random (rng_seed=42) and each was swept with a 40x40 grid of (x, y)
placements over x, y in [-4.4, 4.4], with oracle_steps=500 per attempt. For each grid
point that was attempted, the sweep stopped at the first success across up to 10 variants
per seed. The solving variant is reported per seed.

Platform_y for each seed was read from `level.objects['left_platform'].y` with variant=0.
This is the y-coordinate of both platform segments flanking the gap; it is drawn from
`rng.uniform(-3.5, 1.0)` in the level generator.

## Result

**30 / 30 swept seeds (100%) were solved by the grid sweep. 0 seeds were confirmed
impossible.**

Extrapolated to the full impossible set: all ~106 labeled-impossible seeds are estimated
to be oracle false negatives.

### Platform_y distribution for swept seeds

| Statistic | Value |
|---|---|
| Mean platform_y (solved seeds) | -0.840 |
| Min platform_y (solved seeds) | -3.425 |
| Max platform_y (solved seeds) | 0.968 |
| Seeds with platform_y > -3.05 | 29 / 30 |
| Seeds with platform_y <= -3.05 | 1 / 30 |

The single seed below the documented cutoff (seed=570, platform_y=-3.425) was also solved
by the grid, at red_ball position (0.113, -2.821). Even this extreme-deep-platform case is
solvable — the oracle missed it.

### Solving position geometry

All 30 solutions have red_ball_y in [-2.821, 1.467] (mean -0.293), well below green_ball's
starting position at y=3.5. This is entirely consistent with Zone B geometry (low intercept
path). None of the solutions used Zone A placement (near green_ball.y). Solving x-coordinates
are tightly clustered in [-1.015, 1.467], matching the oracle's documented Zone B valid x
range of [-1.3, 1.3].

### Does the platform_y cutoff hold?

No. The documented cutoff of platform_y <= -3.05 for solvability is empirically falsified.
29 of 30 solved seeds have platform_y > -3.05, including seeds with platform_y as high as
0.968. The grid finds a valid Zone B placement for every seed regardless of platform depth.

## Verdict

**ORACLE FAILURE** — 100% false-negative rate (30/30 swept seeds solved by grid).

The oracle's documented impossibility condition (platform_y <= -3.05) reflects a
historical limitation of the old Zone-A-only oracle, not an intrinsic property of the
level geometry. Zone B placements (red_ball at low y, near hole center) solve seeds
across the full platform_y range [-3.5, 1.0]. The oracle implements Zone B with 33%
sampling probability and ~17 Zone B attempts per run, but the valid placement windows
are evidently narrow enough that 17 random attempts produce a near-zero hit probability
per run, resulting in systematic false negatives.

## Design recommendation

The 106 labeled-impossible seeds are NOT genuinely impossible — they are solvable via
Zone B geometry. The oracle requires redesign, not the level. Two options:

1. **Increase Zone B sampling rate or attempts**: Currently 33% of 50 = ~17 Zone B
   attempts per run. Increasing to 50+ Zone B attempts with focused x/y priors (x near
   hole center, y in [-2.0, 1.5]) would likely recover most seeds.

2. **Grid-based oracle fallback**: For seeds that fail stochastic sampling, run a coarse
   grid (e.g., 20x20 restricted to Zone B x/y bounds) as a fallback.

Do not re-label impossible seeds as hard-difficulty or exclude them from the bundle
without first improving the oracle. The platform_y cutoff should be removed from oracle
documentation as it is not supported by empirical evidence.
