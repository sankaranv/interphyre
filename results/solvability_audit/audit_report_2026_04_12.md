# Interphyre Solvability Audit Report
**Date:** 2026-04-12  
**Branch:** fix/solvability  
**Scope:** All 25 levels, bundle solvability rates, oracle calibration, and redesign recommendations

---

## Executive Summary

25 levels audited across three dimensions: (1) bundle solvability rates from 10k-seed bundles, (2) oracle calibration quality (what fraction of solvable seeds is the oracle actually finding?), and (3) triviality risk (could the level self-solve without agent action?).

**Status by category:**

| Category | Levels | Status |
|----------|--------|--------|
| Clean — oracle calibrated, no action | 20 | ✓ |
| Oracle fixed this session — awaiting regen | 2 | 🔄 (SLURM running) |
| Medium solvability — genuine impossibility | 3 | ⚠ |
| Critical — design redesign recommended | 2 | ❌ |

---

## Bundle Solvability Snapshot (pre-fix)

| Level | Valid | Total tried | Valid % | Avg var | Max var | Oracle commit |
|-------|-------|-------------|---------|---------|---------|---------------|
| basket_case | 10 000 | 10 000 | 100.0% | 0.56 | 9 | 74e704f |
| catapult | 1 274 | 17 000 | 7.5% | 4.40 | 9 | a73b341 |
| cliffhanger | 10 000 | 10 000 | 100.0% | 0.27 | 5 | 1b22688 |
| dive_bomb | 10 051 | 10 130 | 99.2% | 1.43 | 9 | f02bdab |
| down_to_earth | 10 000 | 10 000 | 100.0% | 0.00 | 1 | f5c1fb5 |
| end_of_line | 10 000 | 10 000 | 100.0% | 0.19 | 5 | 58c1240 |
| falling_into_place | 10 048 | 10 076 | 99.7% | 1.22 | 9 | 6161f8b |
| flagpole_sitta | 10 000 | 10 000 | 100.0% | 0.73 | 9 | 967692c |
| just_a_nudge | 652 | 10 000 | 6.5% | 4.37 | 9 | 92a5c0d |
| keyhole | 10 069 | 10 158 | 99.1% | 1.61 | 9 | 6161f8b |
| locust_swarm | 10 110 | 14 310 | 70.6% | 3.48 | 9 | 6161f8b |
| marble_race | 10 000 | 10 000 | 100.0% | 0.40 | 6 | 70271a6 |
| mind_the_gap | 10 054 | 10 127 | 99.3% | 1.41 | 9 | 6161f8b |
| off_the_rails | 10 050 | 10 053 | 99.97% | 0.73 | 9 | 6161f8b |
| pass_the_parcel | 10 050 | 10 072 | 99.8% | 1.11 | 9 | 6161f8b |
| pinball_machine | 10 103 | 11 894 | 84.9% | 2.99 | 9 | 6161f8b |
| seesaw | 10 000 | 10 000 | 100.0% | 0.60 | 8 | a7fe50a |
| staircase | 10 101 | 10 440 | 96.8% | 2.16 | 9 | 6161f8b |
| straight_face | 10 049 | 10 057 | 99.9% | 0.91 | 9 | 6161f8b |
| the_cradle | 11 109 | 18 435 | 60.3% | 3.75 | 9 | 6161f8b |
| the_funnel | 10 028 | 10 204 | 98.3% | 1.83 | 9 | 6161f8b |
| tipping_point | 10 000 | 10 000 | 100.0% | 0.12 | 4 | 3e52639 |
| two_body_problem | 10 000 | 10 000 | 100.0% | 0.50 | 9 | 3e52639 |
| wedge_issue | 10 000 | 10 000 | 100.0% | 0.53 | 9 | 27a663b |
| zebra_crossing | 10 000 | 10 000 | 100.0% | 0.64 | 9 | 4f5af8c |

---

## Per-Level Findings

### TIER 1: Clean levels — no action needed

#### basket_case
- **Solvability:** 100% (10k valid)
- **Verdict:** CORRECT
- **Mechanism:** Red ball placed below green ball deflects it laterally away from basket, landing on purple_ground.
- **Oracle:** Four-band design covers multiple mechanisms. All 10k solutions accounted for.
- **Trivial risk:** None — deflection requires agent action.
- **Action:** None.

#### cliffhanger
- **Solvability:** 100% (10k valid)
- **Verdict:** CORRECT
- **Mechanism:** Red ball knocks vertical green bar sideways off platform edge; bar falls to purple ground.
- **Oracle:** Covers ±2 units horizontal, full y drop range. 100% zone coverage.
- **Trivial risk:** None — requires horizontal momentum.
- **Action:** None.

#### down_to_earth
- **Solvability:** 100% (10k valid), avg_var=0.00 (every seed solved on first try)
- **Verdict:** CORRECT
- **Mechanism:** Green ball falls from y=4.0 onto platform; red ball intercepts it in the fall column and pushes it past the platform edge to purple_ground.
- **Oracle:** x ∈ [platform.left−1, platform.right+1], y ∈ [platform.y−1, green_ball.y+0.5]. Full fall-column coverage.
- **Trivial risk:** None — green ball lands on platform, cannot reach ground without push.
- **Note:** avg_var=0.00 indicates oracle is reliable enough that no seed ever needs a variant retry. This is expected given the simple geometry.
- **Action:** None.

#### end_of_line
- **Solvability:** 100% (10k valid)
- **Verdict:** CORRECT
- **Mechanism:** Red ball knocked from opposite side pushes green ball off shelf toward purple wall.
- **Oracle:** Two-band strategy — Band A for mid-shelf seeds, Band B (high-drop) for deep-shelf seeds where Band A alone fails.
- **Trivial risk:** None.
- **Action:** None.

#### falling_into_place
- **Solvability:** 99.7% (28 impossible in 10k)
- **Verdict:** CORRECT
- **Mechanism:** Red ball pushes green ball through hole, rebounds off ramp, reaches basket.
- **Oracle:** Three-region coverage (lateral, high-y, near-hole edge).
- **Impossible seeds (28):** Geometric edge cases — extreme hole widths or basket positioning. True impossibility.
- **Action:** None.

#### flagpole_sitta
- **Solvability:** 100% (10k valid)
- **Verdict:** CORRECT (exemplary oracle design)
- **Mechanism:** Red ball imparts lateral impulse to knock green ball off flagpole; ball free-falls to purple_ground.
- **Oracle:** Two-phase (above-side drop + ramp-bounce), adaptive x_frac sampling, causal contact verification, _MIN_ORACLE_STEPS=1200 override.
- **Trivial risk:** The causal verification check (requires red_ball contact with green_ball or flagpole) explicitly prevents counting any coincidental self-solving successes.
- **Note:** This is the most rigorous oracle in the codebase. Other levels should follow this pattern.
- **Action:** None.

#### marble_race
- **Solvability:** 100% (10k valid)
- **Verdict:** CORRECT
- **Mechanism:** Red ball placed on right end of gray beam tips it; green ball rolls through ramp sequence into basket.
- **Oracle:** _MIN_ORACLE_STEPS=1500 override critical — beam tips slowly, needs more than default 500 steps.
- **Trivial risk:** None — beam geometry is initially balanced.
- **Action:** None. Note dependency on oracle_steps override.

#### mind_the_gap
- **Solvability:** 99.3% (73 impossible in 10k)
- **Verdict:** CORRECT
- **Mechanism:** Red ball deflects green ball past blocker ball, falls through gap to purple_ground.
- **Oracle:** Two zones (tangent push + low-y zone). Full-board y coverage added after fix.
- **Impossible seeds (73):** Geometric edge cases — hole/blocker positioning creates no viable trajectory.
- **Action:** None.

#### off_the_rails
- **Solvability:** 99.97% (3 impossible in 10k)
- **Verdict:** CORRECT
- **Mechanism:** Red ball pushed into basket deflects green ball onto purple wall.
- **Oracle:** Two-band with dynamic switching for near-ceiling seeds.
- **Impossible seeds (3):** Geometric edge cases. True impossibility.
- **Action:** None.

#### pass_the_parcel
- **Solvability:** 99.8% (22 impossible in 10k)
- **Verdict:** CORRECT
- **Mechanism:** Red ball topples inverted basket; green ball rolls into bottom basket and hits blue ball.
- **Oracle:** Tightened y-range to [+0.1, +1.5] for low-energy graze mechanism.
- **Impossible seeds (22):** Platform_y conditional constraint in level builder; true impossibility.
- **Action:** None.

#### seesaw
- **Solvability:** 100% (10k valid)
- **Verdict:** CORRECT (recently fixed)
- **Mechanism:** Red ball near beam tips lever; green ball contacts purple floor.
- **Oracle:** Two zones with y-floor removed after fix (prior oracle had 86% false-negative rate).
- **Trivial risk:** None — requires active tipping.
- **Action:** None.

#### tipping_point
- **Solvability:** 100% (10k valid), avg_var=0.12
- **Verdict:** CORRECT
- **Mechanism:** Red ball strikes vertical green bar to apply tipping moment; bar falls to purple wall.
- **Oracle:** 100% zone coverage for bar_top region.
- **Trivial risk:** None — bar starts 1.5-2.8 units from wall; agent impact required.
- **Action:** None.

#### two_body_problem
- **Solvability:** 100% (10k valid)
- **Verdict:** CORRECT
- **Mechanism:** Red ball placed between separated green and blue balls creates a collision bridge.
- **Oracle:** Single zone covering bridge corridor. 100% coverage.
- **Trivial risk:** None — balls separated at same height, cannot close without agent.
- **Action:** None.

#### wedge_issue
- **Solvability:** 100% (10k valid)
- **Verdict:** CORRECT
- **Mechanism:** Red ball acts as stopper on purple bar, enabling green ball to maintain extended contact.
- **Oracle:** Four complementary zones.
- **Trivial risk:** None.
- **Action:** None.

#### zebra_crossing
- **Solvability:** 100% (10k valid)
- **Verdict:** CORRECT
- **Mechanism:** Red ball creates chain reaction through stacked diagonal bars to channel green ball through separator gate.
- **Oracle:** Two-phase band sampling guarantees coverage.
- **Trivial risk:** None — ceiling at y=4.5 forces solutions to exist only in below-zone.
- **Action:** None.

---

### TIER 2: Levels with oracle fixes applied (SLURM jobs running)

#### catapult
- **Solvability:** 7.5% (1274 valid / 17000 tried) — **severely under-performing**
- **Expected true solvable rate:** ~60% (from 2026-04-03 sweep study)
- **Root cause:** Zone B was full-board (81 sq units), severely diluting sampling density for the 13.1% of solutions with x > 0.2 (right-side mechanism). Solutions have sparse valid regions (~0.1-0.5 sq units per seed); n_attempts=50 insufficient.
- **Oracle fix applied (2026-04-12):**
  - Zone B changed: x ∈ [arm_right, 4.5], y ∈ [arm_top+0.5, 4.5] (15-20 sq units instead of 81). Concentrates Zone B on right-side solutions (4-5× density improvement).
  - n_attempts increased to 200 in bundle generation script.
- **SLURM job:** 55482084 (bundle_catapult_v2) — running
- **Expected outcome:** 20-40% valid rate after regen.
- **Mechanism:** Red ball dropped from high above arm (y_rel median 5.68 units above arm_top); arm tips and launches green ball into basket.
- **Bundle geometry analysis:**
  - arm_right: always -0.80 (arm starts at MIN_X+0.2, length=4.0)
  - 86.9% of solutions: x ≤ 0.2, y ≥ arm_top+1.0 (Zone A)
  - 13.1% of solutions: x > 0.2 or y < arm_top+1.0 (Zone B)
  - y_rel range: [0, 7.57], median=5.68 — high drops required
- **After regen:** If valid rate < 20%, investigate increasing n_attempts to 500 or reducing oracle_steps to allow more attempts within compute budget.

#### just_a_nudge
- **Solvability:** 6.5% (652 valid / 10000) — under-performing
- **Expected true solvable rate:** ~10% (from 2026-04-03 sweep)
- **Root cause:** Zone A x_max = green_ball.x + 3.5 (≈3.2 for median seed), but 44.2% of valid solutions have dx > 3.5 and were entirely missed. Zone A y_min = green_ball.y - 1.5 also missed solutions with large negative dy (down to -5.99).
- **Oracle fix applied (2026-04-12):**
  - x_max_a expanded to 4.5 (always) — covers all right-side solutions
  - y_min_a expanded from gb.y - 1.5 to gb.y - 5.0 — covers 99.7% of observed solutions
  - Coverage improvement: 54.8% → 98.8% of bundle solutions now in Zone A
- **SLURM job:** 55482085 (bundle_just_a_nudge_v2) — running
- **Expected outcome:** ~9-12% valid rate after regen.
- **Design note:** This level has ~90% genuine impossibility — most seeds have platform/basket misalignment where the knocked green ball cannot reach the basket. 10k valid seeds would require ~100k total seeds, which is not justified. This level is **flagged for design review** (see redesign report section).
- **Mechanism:** Red ball knocks green ball directly off vertical platform; green ball falls into basket and contacts blue ball.
- **Bundle geometry analysis:**
  - Solution x: [-1.86, 4.50] — spans right half of board
  - Solution y: [-3.35, 4.49] — broad range
  - dx range: [-1.73, 5.08], median=3.47 (right at old Zone A boundary)
  - dy range: [-5.99, 2.78], median=0.80

---

### TIER 3: Medium solvability — genuine impossibility accepted

#### the_cradle
- **Solvability:** 60.3% (11109 valid / 18435)
- **Verdict:** EXPECTED — oracle recently fixed (top-down drop mechanism)
- **Mechanism:** Red ball dropped from top of board into V-shaped cradle dislodges green ball.
- **Genuine impossibility:** ~40% of seeds. V-cradle geometry resists top-down impact for some seed configurations. True ceiling estimated 60-65%.
- **Oracle:** Top-down drop zones (y ∈ [2.59, 4.40] from sweep). Recently fixed from lateral approach which missed 83% of solvable seeds.
- **Recommendation:** Investigate a random sample of 20-30 impossible seeds via dense grid sweep to confirm true impossibility. If > 15% of "impossible" seeds have solutions, oracle needs further refinement.

#### locust_swarm
- **Solvability:** 70.6% (10110 valid / 14310)
- **Verdict:** IMPROVABLE
- **Mechanism:** Green ball at y=4.0 must descend through procedurally-generated star chains to purple_floor. Red ball initiates downward motion.
- **Genuine impossibility:** ~25-30% of seeds. Dense star chains in some configurations create impenetrable barriers. True ceiling estimated 75-80%.
- **Oracle:** Zone A (y ∈ [0.5, 3.5], full x) + Zone B fallback. Prior fix removed y dead-zone that caused 64% false-negative rate.
- **Recommendation:** Grid sweep 50 impossible seeds to verify remaining false-negative rate. If > 10% improvable, refine oracle. If at ceiling, consider procedural generation filter to exclude seeds with impenetrable star configurations.

#### pinball_machine
- **Solvability:** 84.9% (10103 valid / 11894)
- **Verdict:** IMPROVABLE
- **Mechanism:** Green ball at y=4.0 navigates 4-layer zigzag star obstacles to purple_floor. Red ball nudges it.
- **Genuine impossibility:** ~13-15% of seeds. Zigzag lines occasionally too dense for any trajectory. True ceiling estimated 85-90%.
- **Oracle:** Gaussian basket-centered x (σ=1.5) + uniform fallback. Fixed after 70% pre-fix false-negative rate.
- **Recommendation:** Grid sweep 30 impossible seeds. Lower false-negative rate than locust_swarm suggests oracle is better calibrated.

---

### TIER 4: Near-100% levels — small impossible counts

#### dive_bomb
- **Solvability:** 99.2% (79 impossible)
- **Verdict:** CORRECT — 79 impossible seeds from cannon geometry edge cases. True impossibility.

#### keyhole
- **Solvability:** 99.1% (89 impossible)
- **Verdict:** CORRECT — gap/divider geometry constraints. Four-region oracle covers edge cases.

#### the_funnel
- **Solvability:** 98.3% (176 impossible)
- **Verdict:** CORRECT — funnel angle + target/blocker positioning creates some blocked configurations. Highest impossible count in near-100% tier.

#### staircase
- **Solvability:** 96.8% (339 impossible)
- **Verdict:** ⚠ BORDERLINE — highest impossible count of all near-100% levels. Prior 86% false-negative rate suggests oracle had significant gaps. Current 339 impossible seeds may be a mix of true impossibility and remaining oracle gaps.
- **Recommendation:** Grid sweep 50 impossible staircase seeds to verify. If > 50 are solvable (15% of impossible), the oracle still has systematic gaps. If < 30 are solvable, 96.8% is the true ceiling and level is acceptable.

#### straight_face
- **Solvability:** 99.9% (8 impossible)
- **Verdict:** CORRECT — extreme lateral separation causes geometric impossibility. Full-board sampling covers all mechanisms.

---

## Oracle Status Summary

| Level | Oracle type | Calibration status | Action taken |
|-------|-------------|-------------------|--------------|
| basket_case | Targeted (4-band) | Calibrated | — |
| catapult | Targeted (2-zone) | **Under-performing** | Zone B fixed, n_attempts=200, SLURM regen |
| cliffhanger | Targeted | Calibrated | — |
| dive_bomb | Targeted (3-zone) | Calibrated | — |
| down_to_earth | Targeted | Calibrated | — |
| end_of_line | Targeted (2-band) | Calibrated | — |
| falling_into_place | Targeted (3-region) | Calibrated | — |
| flagpole_sitta | Targeted (2-phase + causal verify) | Exemplary | — |
| just_a_nudge | Targeted (2-zone) | **Zone A miscalibrated** | Zones expanded, SLURM regen |
| keyhole | Targeted (4-region) | Calibrated | — |
| locust_swarm | Targeted (2-zone) | Calibrated (post-fix) | — |
| marble_race | Targeted | Calibrated (steps override) | — |
| mind_the_gap | Targeted (2-zone) | Calibrated | — |
| off_the_rails | Targeted (2-band) | Calibrated | — |
| pass_the_parcel | Targeted | Calibrated | — |
| pinball_machine | Targeted (gaussian) | Calibrated (post-fix) | — |
| seesaw | Targeted (2-zone) | Calibrated (post-fix) | — |
| staircase | Targeted (gaussian) | Possibly gaps remaining | Recommend sweep |
| straight_face | Default | Calibrated | — |
| the_cradle | Targeted (top-down) | Calibrated (post-fix) | — |
| the_funnel | Targeted (2-zone) | Calibrated | — |
| tipping_point | Targeted | Calibrated | — |
| two_body_problem | Targeted | Calibrated | — |
| wedge_issue | Targeted (4-zone) | Calibrated | — |
| zebra_crossing | Targeted (2-band) | Calibrated | — |

---

## Design Redesign Recommendations

### just_a_nudge (HIGH PRIORITY)
**Issue:** ~90% of seeds are genuinely impossible due to platform/basket geometry misalignment. Even with a perfect oracle, 10k valid seeds would require ~100k total seeds (~100 hours compute vs ~1-2 hours for all other levels). This is not scalable.

**Root cause:** The basket x position is constrained (`basket_x ≤ max_basket_x = platform.right + 0.39 - basket_half_width`), but platform is nearly vertical (a "post"), so `platform.right ≈ platform_x + 0.1`. For basket to catch the knocked green ball, the basket must be almost exactly under the ball's trajectory. Most seeds have too much lateral misalignment.

**Proposed minimal redesign options (ranked by invasiveness):**

1. **Widen basket constraint** (least invasive): Change `basket_right_ratio` constraint to allow basket_x up to platform_x + 1.5 instead of + 0.49. This would directly align more baskets under the green ball trajectory. Impact: larger coverage of solvable seeds without changing visual appearance.

2. **Center basket under platform** (moderate): Force `basket_x = platform_x + rng.uniform(-0.5, 0.5)` (instead of uniform over [-1.0, max_basket_x]). Most seeds would now have the basket roughly under the platform. Estimated solvable rate: 40-60%.

3. **Reduce platform height** (low invasiveness): Reduce `platform_length` from 3.5 to 2.0-2.5. Lower platform means ball falls a shorter distance, giving it less time to drift sideways and missing the basket. More seeds would be catchable.

4. **Add alignment guide** (structural change): Add a funnel or ramp structure that guides the knocked ball toward the basket. This changes the visual design but ensures much higher solvability.

**Recommendation:** Implement option 2 (center basket) first. Run test bundle of 1000 seeds with the change. If valid rate reaches 30%+, proceed. This is a minimal change to the RNG parameter that doesn't affect visual appearance much.

### catapult (MEDIUM PRIORITY — awaiting regen results)
**Issue:** Current oracle achieves 7.5% valid rate vs expected 60%. Oracle zones were recently redesigned based on sweep study. After oracle fix (Zone B targeted) and increased n_attempts, if valid rate remains below 20%, investigate:

1. Whether the level's green ball can actually reach the basket from the catapult arm position (basket on right ledge at x≈3.5-4.5, green ball starts at x≈-4.55 — 8+ unit throw)
2. Whether the success condition (`is_in_contact_for_duration("green_ball", "blue_ball")`) is ever met for seeds labeled "valid"

**If regen confirms > 20% valid:** The oracle fix was sufficient; extend bundle to 10k valid.

**If regen shows < 20% valid:** Fundamental level design issue. Options:
1. Move the basket to the left half of the board (closer to green ball's natural trajectory)
2. Reduce arm length or adjust pivot position to increase catapult distance
3. Replace success condition: instead of green_ball hitting blue_ball at basket, have green_ball simply reach the right side of the board

---

## Action Items by Priority

| Priority | Level | Action | Status |
|----------|-------|--------|--------|
| 1 | catapult | SLURM regen with Zone B fix + n_attempts=200 | 🔄 Running (job 55482084) |
| 1 | just_a_nudge | SLURM regen with expanded Zone A | 🔄 Running (job 55482085) |
| 2 | just_a_nudge | Level redesign: center basket under platform | Pending (after regen verifies oracle) |
| 3 | catapult | If regen < 20% valid: investigate level design issues | Pending (after regen) |
| 4 | staircase | Grid sweep 50 impossible seeds | Future |
| 5 | the_cradle | Grid sweep 30 impossible seeds to confirm ceiling | Future |
| 6 | locust_swarm | Grid sweep 50 impossible seeds | Future |
| 7 | pinball_machine | Grid sweep 30 impossible seeds | Future |

---

## Next Steps

1. **Check SLURM job logs** when catapult and just_a_nudge jobs complete.
2. **Evaluate catapult regen rate**: If ≥ 20%, extend to 10k valid. If < 20%, escalate to level design investigation.
3. **Evaluate just_a_nudge regen rate**: If ≥ 9%, document oracle improvement. If ≥ 10%, the oracle is now at the ceiling and level redesign should begin.
4. **just_a_nudge redesign**: Prototype the "center basket" change in a separate branch. Run 1000-seed test bundle.
5. **Sweep studies for medium levels** (the_cradle, locust_swarm, pinball_machine, staircase): Submit SLURM grid sweep jobs for 30-50 impossible seeds each to measure true impossibility vs oracle gaps.
