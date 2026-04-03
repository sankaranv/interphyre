# the_funnel sweep study

**Date:** 2026-04-03  
**Seeds swept:** 93 of 93 impossible  
**Grid:** 40×40, variants: 10, oracle_steps: 500

## Hypothesis

Zone B's 40% allocation of 200 attempts (80 samples) may miss narrow valid windows when
the green_ball is strongly misaligned with the target side. The prior expected a
mixed-to-moderate false-negative rate, with some seeds genuinely impossible.

## Setup

The sweep loaded all 93 seeds labeled "impossible" in the current the_funnel bundle
(oracle_commit b13317b). For each seed, up to 10 variants were tested; within each
variant a 40×40 grid of (x, y) positions spanning the full board [-4.4, 4.4]² was
tried at 500 simulation steps per attempt. Any grid success classifies the seed as an
oracle false negative. The grid spacing is 8.8/39 ≈ 0.226 units, resolving valid
windows of radius ≥ 0.11 units. Seeds requiring windows narrower than one grid cell
cannot be detected by this method, making the false-negative count a lower bound.

## Result

**93 / 93 swept seeds (100.0%) were solved by the grid. 0 seeds confirmed impossible.**

Winning positions cluster in two board regions:

- **Upper board** (y ∈ [2.37, 4.40], n=54, 58%): mean position (x=-0.95, y=3.29).
  These placements require the red ball to drop far above the funnel mouth, entering
  the funnel from a high arc.
- **Lower board** (y ∈ [-4.40, -3.50], n=38, 41%): mean position (x=-0.32, y=-4.19).
  These are floor-level placements; the red ball collides with the funnel structure
  from below or reaches the target via a floor bounce.
- **Mid board** (|y| < 2.0, n=1, 1%).

x coordinates for both clusters are centered near -0.7 (slightly left-biased across
the full sample), consistent with a left-target prevalence or left-leaning geometry.

**Root cause — systematic oracle y-range collapse:**

The bundle was generated with the oracle at commit b13317b, whose y-sampling was:

```
y_min = clip(green_ball.y - 0.3, -4.5, 4.5)  # = 4.40  (green_ball.y ≈ 4.70)
y_max = clip(green_ball.y + 2.0, -4.5, 4.5)  # = 4.50
```

This produced a **0.10-unit y strip** at the top of the board. For 92/93 seeds, the
valid placement lies entirely outside [4.40, 4.50], so the probability of an oracle
success per attempt was identically zero — not low, but zero. The oracle could not
solve these seeds regardless of the number of attempts, because the valid y-region
was not in its sampling support.

The oracle fix (Zone A + Zone B) was committed at b9a11eb (35 minutes after b13317b)
but the the_funnel bundle was not regenerated with the corrected oracle. The current
bundle still records oracle_commit=b13317b and retains all 93 false-negative seeds.

## Verdict

**ORACLE FAILURE** — 100% of impossible-labeled seeds are oracle false negatives.
The old oracle's y-sampling window [4.40, 4.50] has zero overlap with valid placements
for 92/93 seeds; this is a systematic design flaw, not probabilistic bad luck.

## Design recommendation

**Regenerate the the_funnel bundle using the current oracle (Zone A 60% + Zone B 40%).**
The current oracle already has the correct fix: Zone B samples the full board y ∈ [-4.5, 4.5],
which covers both the upper-board cluster (y ∈ [2, 4.2]) and the lower-board cluster
(y ∈ [-4.4, -3.5]). Based on the prior fix rationale and sweep success rate, the
regenerated bundle should recover most or all of these 93 seeds as valid, reducing
the impossible rate from 9.3% to near 0%.

No oracle code changes are required — only a bundle regen at HEAD.
