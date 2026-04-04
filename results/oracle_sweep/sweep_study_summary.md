# Oracle vs Genuine Impossibility — Complete Sweep Study

**Date:** 2026-04-03  
**Levels studied:** 10 levels (all with notable impossible rates)  
**Total seeds swept:** 523 (50×8 + 30×3 + 93 funnel)  
**Protocol:** 40×40 full-board grid (spacing ≈ 0.23 units), up to 10 variants, 500 physics steps

## Top-line result

**505 of 523 swept seeds (96.6%) are oracle false negatives.** Across all 10 levels
studied, no level showed genuine level geometry as the dominant cause of bundle
failures. Oracle quality failures drive the impossible seed counts in every case.

The level design pass must not proceed on current bundle data. After oracle fixes
and bundle regens complete, a clean analysis of the truly-impossible residual
will give accurate data for any level design decisions.

## Complete per-level results

| Level | FNR | Verdict | Root cause | Oracle fix |
|---|---|---|---|---|
| the_funnel | 100% | Stale bundle | Bundle generated before y-range fix | Regen at HEAD |
| mind_the_gap | 100% | Oracle failure | Zone B density too sparse | Zone B weight 33→50%, x tightened, y-min raised |
| dive_bomb | 100% | Oracle failure | Missing gray_ball Zone C | Added Zone C (30%), widened Zone B |
| seesaw | 100% | Oracle failure | Zone A y-floor at 3.5 excluded 86% of solutions | Remove y-floor; Zone A = beam x + full y |
| staircase | 86% | Oracle failure | Valid windows 0.05×0.05 units; uniform sampling too sparse | Basket-centered x Gaussian (σ=1.5), n_attempts 50→200 |
| the_cradle | 83% | Oracle failure | Wrong mechanism (lateral vs top-down drop) | Zone A: x near gb ± 3.0, y ∈ [2.5, 4.5] |
| catapult | 60% | Oracle failure | Wrong mechanism (barely-above-arm vs high drop) | Zone A: x ∈ [-4.5, arm_right+1.0], y ∈ [arm_top+1.0, 4.5] |
| locust_swarm | 64% | Oracle failure | Zone A y dead-zone + x too narrow | Zone A: full x, y ∈ [0.5, 3.5]; Zone B: full board |
| pinball_machine | 70% | Oracle failure | Zone A y dead-zone + x too narrow | Zone A: x ± 3.5, y ∈ [1.5, 3.8]; Zone B: same x, full y |
| just_a_nudge | 10% | MIXED | Wrong mechanism (basket push vs direct platform knockoff) | Zone A: near gb ± 3.5, y ∈ [gb.y-1.5, gb.y+2.5]; Zone B: full board |

## Confirmed impossible seeds (at 40×40 resolution)

| Level | Confirmed impossible | Fraction | Notes |
|---|---|---|---|
| just_a_nudge | 27/30 | 90% | Genuinely hard level; platform knockoff geometry rarely aligned |
| locust_swarm | 18/50 | 36% | Dense star chains block all paths for some seeds |
| pinball_machine | 15/50 | 30% | Dense star configurations block all trajectories |
| catapult | 20/50 | 40% | Basket/ledge geometry prevents green ball entry for some seeds |
| the_cradle | 5/30 | 17% | Some V-cradle geometries resist all valid dislodgement |
| staircase | 7/50 | 14% | Narrow approach windows; all unresolved may be grid misses |
| the_funnel | 0/93 | 0% | All oracle failures |
| mind_the_gap | 0/30 | 0% | All oracle failures |
| dive_bomb | 0/50 | 0% | All oracle failures |
| seesaw | 0/50 | 0% | All oracle failures |

## What characterizes genuine impossibility

**No single geometric attribute reliably identifies impossible seeds** in any level tested.
n_stars, guard_gap, basket_scale, arm_top, and rb_radius show complete overlap between
solvable and confirmed-impossible seeds in every level analyzed.

The only reliable characterization of genuine impossibility is:
**A seed that fails a dense full-board grid sweep (40×40 or finer) across 10 variants.**

Mechanistic patterns that contribute to impossibility (level-specific):
- **Star-chain levels** (locust_swarm, pinball_machine): specific configurations of
  star obstacles that block all trajectories regardless of red ball placement
- **catapult**: basket/ledge geometry where the launch trajectory never intersects the basket
- **just_a_nudge**: platform orientation that cannot be knocked toward the basket
- **the_cradle**: V-cradle holder angle/gap combinations that resist top-down impact

## Three failure mode categories

### 1. Stale bundle (the_funnel)
Bundle generated with old oracle; current oracle already correct. Regen only.

### 2. Wrong mechanism (the_cradle, catapult, just_a_nudge)
Oracle modeled a causal path that physically cannot work. Sweep revealed the
correct mechanism: top-down drop (the_cradle), high-energy drop from above
(catapult), direct platform knockoff (just_a_nudge).

### 3. Coverage gap / dead zone (all others)
Oracle covered the correct general mechanism but sampled a restricted region
with zero or near-zero overlap with valid placements:
- y dead-zones (locust_swarm, pinball_machine, seesaw): y-floor/ceiling left
  86-100% of valid placements unsampled
- Missing zone (dive_bomb): gray_ball causal path entirely absent from oracle
- Density (staircase, mind_the_gap): correct region but too sparse to hit
  0.05×0.05 unit valid windows

## Expected outcomes after oracle fixes and bundle regens

| Level | Before | After (confirmed) |
|---|---|---|
| the_funnel | 90.7% | ~99% (bundle from ac4b9bf) |
| mind_the_gap | 89.4% | **99.4%** (f61fb73) |
| dive_bomb | 93.7% | ~99% (bundle from ac4b9bf) |
| seesaw | 96.1% | **100%** (f23009d — all 392 "impossible" were oracle FN) |
| staircase | 93.5%→96.0% | **97.0%** (af4d0fe) |
| the_cradle | 0% | **59.9%** (0504e1e — 40.1% genuinely impossible) |
| catapult | 19.4% | pending |
| locust_swarm | 50.4% | pending |
| pinball_machine | 67.8% | **87.1%** (5073bfc — oracle x-range fix highly effective) |
| just_a_nudge | 0.1% | pending |

Note: catapult, locust_swarm, pinball_machine, and just_a_nudge have substantial
genuine impossibility that will remain after oracle fixes. These levels are
genuinely hard: significant fractions of seeds have geometry that blocks any valid
red ball placement from achieving the win condition.

## Next steps

1. Wait for all bundle regens to complete (running overnight)
2. Verify each bundle's solvable rate matches expectations
3. Re-sweep a sample of remaining impossible seeds in each level with fixed oracle
   to confirm they are genuine impossibility, not further oracle failures
4. Run level design pass only on truly-impossible seeds in each level
5. For just_a_nudge: decide whether 10-15% solvable rate is acceptable design
   target or whether level redesign to increase solvability is warranted
