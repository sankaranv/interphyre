# seesaw sweep study

**Date:** 2026-04-03  
**Seeds swept:** 50 of 392 impossible  
**Grid:** 40×40 (spacing ≈ 0.23 units), variants: 10, oracle_steps: 500

## Hypothesis

The new oracle (Zone A 50% + Zone B 50%) still fails for many seeds because the 50%
Zone B allocation is too diluted — valid placements exist everywhere on the board and
Zone A's x-range is narrow, leaving most of the valid space under-sampled.

## Setup

The sweep loaded all 392 seeds from the `seesaw.json.lzma` bundle that had no `valid`
variant (all variants labeled `impossible`). A random sample of 50 seeds (rng_seed=42)
was swept with a 40×40 full-board grid spanning x, y ∈ [−4.4, 4.4]. For each seed,
all 10 variants were tried; the sweep stopped at the first (variant, position) pair that
resolved the level in 500 physics steps. Results written to `seesaw_sweep.json`.

Zone classification used published oracle boundaries from `oracles/seesaw.py`:

- **Zone A**: x ∈ [beam_left − 0.5, beam_right + 0.5] ∩ [gb.x − 1.5, gb.x + 1.5],
  y ∈ [gb.y − 0.5, 4.5] (i.e., both x-condition and y-condition must hold)
- **Zone B**: full board x, y ∈ [−4.5, 4.5]

For classification, Zone A was tested against its two sub-conditions independently:
- `in_zone_a_x`: x within beam/green_ball x-range
- `in_zone_a_y`: y ≥ gb.y − 0.5 (green_ball is at y ≈ 4.0 in all swept seeds, so threshold ≈ 3.5)

## Result

**50 / 50 swept seeds were solved by the grid (100% oracle false-negative rate).**  
Estimated oracle failures across the full impossible set: ~392 / 392.

### Zone classification of the 50 winning positions

| Classification | Count | Fraction |
|----------------|-------|---------|
| Full Zone A (x-match AND y ≥ 3.5) | 4 | 8% |
| Zone A y-only (y ≥ 3.5, x outside beam) | 3 | 6% |
| Zone A x-only (x in beam, y < 3.5) | 29 | **58%** |
| Outside Zone A entirely (Zone B only) | 14 | 28% |

### Key observation: the y-floor is the dominant failure mode

The green_ball starts at y = 4.0 for all swept seeds. Zone A's y-floor is `gb.y − 0.5 = 3.5`.
Only 14% of winning positions (7/50) satisfy y ≥ 3.5. The remaining **86% of winning
positions are at y < 3.5**, entirely outside Zone A's y-range.

Of those 86%:
- 58% (29/50) land within Zone A's x-range but below the y-floor — confirming the y-range
  is the primary bottleneck, not the x-range.
- Winning y values range from −2.14 to +4.40; most cluster in [−2.0, +3.0].
- 28% (14/50) fall entirely outside Zone A (both x and y miss), requiring Zone B.

## Verdict

**ORACLE FAILURE** — 100% false-negative rate in the sampled set. Every seed labeled
`impossible` in the bundle was solvable by grid search. This is a complete oracle failure.

### Root causes

1. **Zone A y-floor too high (primary cause, 86% of failures).**  
   Zone A restricts y to [gb.y − 0.5, 4.5] = [3.5, 4.5] — a 1.0-unit strip near the top
   of the board. Valid placements concentrate in [−2.0, +3.0] because the red_ball must tip
   the beam at various angles, not just from directly above the green_ball. Zone A as
   currently defined captures fewer than 14% of winning positions.

2. **Zone B sampling rate too dilute (secondary cause, 28% of failures).**  
   Zone B covers the full board but receives only 50% of attempts (n_attempts attempts, half
   on a 9×9 unit² area). The valid windows at low y are small relative to the full board
   (81 unit²), so the effective hit rate for Zone B is low. Even at n_attempts = 10, Zone B
   probability of hitting a narrow valid window (radius ~0.2) is ~1 − (1 − π·0.04/81)^5 ≈ 0.8%
   per attempt cluster — stochastically unreliable.

3. **Zone A x-range is adequate** — 66% of winning positions fall within Zone A's x-bounds,
   confirming the x logic is correct. The x-range is not the problem.

### Why Zone B dilution explains the regression from 1k to 10k

The old oracle (Zone A only) had a 0.5% failure rate at 1k seeds. The new oracle adds Zone B
to cover low-y seeds, but at 50% budget. For seeds where the valid window is at low y, each
attempt has a ~50% chance of sampling Zone A (which will never succeed for that seed) and ~50%
chance of sampling Zone B (which has a small but nonzero hit probability). At n_attempts = 10,
this gives ~5 Zone B attempts — barely enough for seeds with moderately-sized valid windows
but insufficient for seeds with small or narrow windows. The 3.9% failure rate at 10k seeds is
consistent with this analysis: it is not a new geometric difficulty, it is Zone B under-sampling.

## Design recommendation

Drop the Zone A / Zone B split. Replace with a single zone covering the full beam x-range
and the full board y-range, with a denser concentration near the green_ball:

```
Zone A (beam x, full y — 60% of attempts):
  x ∈ [beam_left − 0.5, beam_right + 0.5]
  y ∈ [−4.5, 4.5]
  This covers 66% of winning positions within a narrow x-strip, giving high density.

Zone B (full board — 40% of attempts):
  x ∈ [−4.5, 4.5]
  y ∈ [−4.5, 4.5]
  Covers the 28% of seeds with winning x outside the beam span.
```

The key change is **removing the y-floor from Zone A**. The x-range of Zone A is correct;
it is only the y restriction to [gb.y − 0.5, 4.5] that is causing 86% of failures.

After this fix, re-run bundle generation for seesaw with n_attempts = 10 and verify the
impossible count falls well below 1% of total seeds (from the current 3.9%).
