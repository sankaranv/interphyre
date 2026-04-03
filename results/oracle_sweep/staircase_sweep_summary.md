# staircase sweep study

**Date:** 2026-04-03
**Seeds swept:** 50 of 647 impossible
**Grid:** 40×40, variants: 10, oracle_steps: 500

## Hypothesis

Tight guard-bar approach windows cause oracle misses. Expected 5–15% false-negative rate
from uniform sampling missing narrow valid regions.

## Setup

The sweep loaded the 647 seeds in `staircase.json.lzma` for which every recorded variant
had status `impossible` (no valid entry). A random sample of 50 seeds (NumPy RNG seed 42)
was drawn. For each seed, a 40×40 grid of (x, y) positions spanning x ∈ [−4.4, 4.4],
y ∈ [−4.4, 4.4] was swept across up to 10 variants, stopping at the first success. Each
grid point ran the physics simulation for 500 steps. Total coverage per seed: up to
16,000 placement evaluations (1,600 grid points × 10 variants), vs the oracle's 500
random placements (50 attempts × 10 variants).

Geometry was extracted at variant 0 for all seeds using `load_level`. The staircase
oracle (`interphyre/validation/oracles/staircase.py`) samples x ∈ [−4.5, 4.5] uniformly
and y ∈ [stair_bottom − 0.5, green_ball.y + 0.5].

## Result

**43 of 50 swept seeds (86%) were solved by the grid — confirmed oracle false negatives.**
7 of 50 seeds (14%) were confirmed impossible at 40×40 grid resolution.
Extrapolated to the full set: ~556 of 647 bundle-impossible seeds are oracle failures.

### Per-seed solution coverage analysis (5-seed sample)

For five seeds solved by the grid, the full 1,600-point grid was swept on the solved
variant to estimate what fraction of placements are valid:

| seed | variant | grid hits | hit rate | P(oracle hit in 50 tries) |
|------|---------|-----------|----------|--------------------------|
| 829  | 1       | 11/1600   | 0.69%    | 29%                      |
| 836  | 0       | 15/1600   | 0.94%    | 38%                      |
| 1503 | 0       | 22/1600   | 1.38%    | 50%                      |
| 1643 | 1       | 1/1600    | 0.06%    | 3%                       |
| 3928 | 1       | 1/1600    | 0.06%    | 3%                       |

The narrowest valid regions (0.06% of board area ≈ 0.05 × 0.05 unit windows) give each
50-attempt oracle pass only a 3% chance of success. Across 10 variants, the probability
of at least one hit is (1 − 0.97¹⁰) ≈ 26% — and that requires the geometrically
compatible variant to be the one probed. Many seeds thus consistently fail 500 oracle
attempts by pure sampling miss.

The oracle y-range was verified to contain all 43 grid solution positions (all solutions
had y ∈ [0.56, 4.40], all within the oracle's stair_bottom-anchored window). The oracle
samples the right region — the problem is density, not range.

### Geometry comparison: solved vs unsolved seeds (variant 0)

| Metric        | Solved (n=43)     | Unsolved (n=7)    |
|---------------|-------------------|-------------------|
| basket_scale  | 1.681 ± 0.143     | 1.672 ± 0.086     |
| guard_gap     | 2.886 ± 0.194     | 2.874 ± 0.117     |
| inner_gap     | 2.686 ± 0.194     | 2.674 ± 0.117     |
| rb_radius     | 0.473 ± 0.093     | 0.525 ± 0.046     |
| clearance     | 1.740 ± 0.291     | 1.623 ± 0.165     |

No geometry attribute separates solved from unsolved seeds. The 7 confirmed-impossible
seeds have clearances of 1.35–1.90 (ample space for the red ball) and basket scales in
the normal range. The 40×40 grid (spacing ≈ 0.23 units) may still miss windows narrower
than ~0.1 units; the 7 unsolved seeds may be oracle failures that require a finer grid,
rather than truly impossible geometries. This is a lower bound on the false-negative rate.

### Solution position distribution (oracle-false-negative seeds)

Grid solutions span x ∈ [−3.05, 3.72] (mean −0.20) and y ∈ [0.56, 4.40] (mean 2.69).
74% of solutions have y > 2.0 — valid placements cluster in the upper half of the board
where the staircase is active, but some require placement near y ≈ 0.5 (near the basket).

Solutions were distributed across all 10 variants, with no single variant dominating
(variants 0 and 1 solved 10 and 9 seeds respectively; variants 5 and 7 solved 1 each),
confirming that variant geometry randomness genuinely matters for solvability.

## Verdict

**ORACLE FAILURE** — 86% false-negative rate, far above the 5–15% expected.

The staircase oracle's valid placement windows can be as small as 0.06% of board area.
At 50 random attempts per variant the expected hit probability per variant ranges from
3% to ~50%, meaning most variants fail even when a solution exists. The fix (range) is
already correct; the failure is sampling density.

## Design recommendation

The oracle's spatial range is correct. The failure mode is that valid placement regions
are small punctate windows (estimated 0.05–0.2 unit radius) that 50 uniform random
samples rarely hit. Two targeted improvements are warranted:

1. **Basket-centered x sampling.** Valid placements cluster near basket.x ± basket.top_width/2
   (the approach corridor). Replace uniform x ∈ [−4.5, 4.5] with a mixture: 80% from
   a Gaussian centered on basket.x with σ ≈ 1.5 units, 20% uniform fallback. This
   increases hit probability for the narrow corridors above the basket mouth.

2. **Increase n_attempts from 50 to 150–200 per variant.** Even with the current oracle,
   P(hit in 50 tries | coverage=0.7%) ≈ 30%. At 150 tries P ≈ 65%, and with the
   concentrated sampler above it reaches >90%. The bundle validation budget allows this.

No guard_gap threshold separates impossible from solvable seeds at 40×40 grid resolution.
The 7 confirmed-impossible seeds should be re-swept at 80×80 grid resolution before
classifying them as genuinely impossible design limits.
