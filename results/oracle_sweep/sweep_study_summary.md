# Oracle vs Genuine Impossibility — Sweep Study Summary

**Date:** 2026-04-03  
**Levels studied:** the_funnel, mind_the_gap, dive_bomb, staircase  
**Total seeds swept:** 223 (93 + 30 + 50 + 50)  
**Script:** `scratch/oracle_hardening/impossible_seed_sweep.py`  
**Protocol:** 40×40 full-board grid (spacing ≈ 0.23 units), up to 10 variants, 500 physics steps per attempt

## Top-line result

**216 of 223 swept seeds (97%) are oracle false negatives.** Not a single level showed
genuinely impossible geometry as the primary cause of bundle failures. The planned level
design pass is premature — the impossible seed counts in the current bundles do not
reflect hard level geometry limits, they reflect oracle quality failures.

## Per-level results

| Level | Bundle impossible | Swept | Grid-solved | False-neg rate | Root cause category |
|---|---|---|---|---|---|
| the_funnel | 93 / 1000 (9.3%) | 93 | 93 (100%) | 100% | Stale bundle |
| mind_the_gap | 106 / 1000 (10.6%) | 30 | 30 (100%) | 100% | Sampling density |
| dive_bomb | 629 / 10,000 (6.3%) | 50 | 50 (100%) | 100% | Coverage gap (missing zone) |
| staircase | 647 / 10,000 (6.5%) | 50 | 43 (86%) | 86% | Sampling density |

7 staircase seeds were not solved at 40×40 grid resolution but show no distinguishing
geometry (basket_scale, guard_gap, clearance all within normal range). These are likely
further oracle misses at finer resolution, not genuine impossibility. Recommend re-sweeping
at 80×80 before accepting any as genuine level design limits.

## Three distinct failure modes

### 1. Stale bundle (the_funnel)

**Action: regen bundle at HEAD — no oracle code changes needed.**

The the_funnel bundle was generated at commit b13317b with a y-sampling window of
[4.40, 4.50] (0.10 units). The oracle fix (Zone A 60% + Zone B full-board) was committed
35 minutes later at b9a11eb but the bundle was never regenerated. The current oracle code
is already correct. All 93 impossible seeds are solved by the grid; winning positions
cluster at y ∈ [2.37, 4.40] (58%) and y ∈ [-4.40, -3.50] (41%) — both outside the old
oracle's dead-zero y-strip.

### 2. Coverage gap (dive_bomb)

**Action: add Zone C (gray_ball region) to oracle, widen Zone B, regen bundle.**

The oracle's documented causal chain omits `gray_ball` as a launch intermediary. 38% of
valid placements lie in a region centered on gray_ball (gray.x ± 2.0, y ∈ [gray.y−0.5,
gray.y+2.5]) that no sampling zone covers. The remaining valid placements fall in Zone A
(30%) or Zone B (32%), with 6% just outside Zone B's x-boundary.

Prescribed oracle changes:
```
Zone A (50%): above green_ball — keep geometry, adjust weight from 70% to 50%
Zone B (20%): ramp region — widen x from ±2.0 to ±3.0, y-floor from -2.5 to -3.5
Zone C (30%): gray_ball region — NEW
  x ∈ [gray.x − 2.0, gray.x + 2.0]
  y ∈ [gray.y − 0.5, gray.y + 2.5]
```

### 3. Sampling density (mind_the_gap, staircase)

**Action: increase Zone B sample concentration and/or n_attempts, regen bundles.**

Both levels have oracles that cover the correct spatial region but sample too sparsely
to reliably hit narrow valid windows.

**mind_the_gap:** Zone B (33% of 50 attempts ≈ 17 samples/run) targets x near hole
center and y below green_ball — the correct region. But all 30 solutions cluster at
x ∈ [-1.015, 1.467], y ∈ [-2.821, 1.467], a sub-region of Zone B. The effective
searchable area is larger than the valid window, so 17 random samples per run produces
near-zero per-run hit probability for the narrowest windows. Fix: tighten Zone B x to
hole_cx ± 1.5 (from ±2.0), increase Zone B weight to 50%, increase n_attempts to 100.

**staircase:** Valid placement windows are as small as 0.05 × 0.05 units (0.06% of board
area), giving a 3% per-pass hit rate at 50 uniform attempts. The oracle's y-range is
correct (all 43 grid solutions fall within it). Fix: replace uniform x with 80% Gaussian
centered on basket.x (σ ≈ 1.5 units) + 20% uniform fallback; increase n_attempts from
50 to 150–200.

## Impact on the level design pass

**The planned design pass should not proceed on current bundle data.** Current impossible
seed counts overstate genuine impossibility by a factor of ~10 or more. After oracle fixes
and bundle regens:

- the_funnel: ~93 seeds recovered → target <1% impossible
- mind_the_gap: ~106 seeds recovered → target <3% impossible  
- dive_bomb: ~629 seeds recovered → target <1% impossible
- staircase: ~556–647 seeds recovered → target <2% impossible

Once bundles are regenerated with improved oracles, a clean pass over the truly-impossible
residual (expected <1–3% per level) will give accurate data for the level design pass.
At that point the remaining impossible seeds will represent genuine geometric constraints
worth addressing in level redesign.

## Next steps (priority order)

1. **the_funnel** — regen bundle at HEAD, no code changes (immediate, ~5 min)
2. **dive_bomb** — add Zone C to oracle, widen Zone B, regen bundle
3. **mind_the_gap** — tighten Zone B, increase n_attempts, regen bundle
4. **staircase** — basket-centered x sampling, increase n_attempts, regen bundle
5. Re-sweep the 7 staircase confirmed-impossible seeds at 80×80 grid resolution
6. Run level design pass on regenerated bundles
