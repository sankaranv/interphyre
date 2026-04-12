# Bundle Audit — 2026-04-12

## Summary

25 levels audited. Valid-seed counts measured per unique seed (not per entry).
Oracle quality has been confirmed for all levels except catapult and just_a_nudge
(stale 1 k bundles, pre-fix oracle).

---

## Status by level

### Complete — 10 000 valid seeds, oracle confirmed

| Level | Valid | Seeds tried | Valid % | oracle_commit |
|---|---|---|---|---|
| basket_case | 10 000 | 10 000 | 100.0% | 74e704f |
| cliffhanger | 10 000 | 10 000 | 100.0% | 1b22688 |
| down_to_earth | 10 000 | 10 000 | 100.0% | f5c1fb5 |
| end_of_line | 10 000 | 10 000 | 100.0% | 58c1240 |
| flagpole_sitta | 10 000 | 10 000 | 100.0% | 967692c |
| marble_race | 10 000 | 10 000 | 100.0% | 70271a6 |
| seesaw | 10 000 | 10 000 | 100.0% | a7fe50a (f23009d regen) |
| tipping_point | 10 000 | 10 000 | 100.0% | 3e52639 |
| two_body_problem | 10 000 | 10 000 | 100.0% | 3e52639 |
| wedge_issue | 10 000 | 10 000 | 100.0% | 27a663b |
| zebra_crossing | 10 000 | 10 000 | 100.0% | 4f5af8c |

All 11 levels have high valid rates with no known oracle gaps. No action needed.

---

### Near-complete — oracle confirmed, small top-up needed

Bundle covers seeds 0–9 999. Valid rate ≥ 97%. A short extension
(seeds 10 000+) will reach 10 000 valid.

| Level | Valid | Missing | Valid % | Extra seeds est. |
|---|---|---|---|---|
| off_the_rails | 9 997 | 3 | ~100% | ~13 |
| straight_face | 9 994 | 6 | 99.9% | ~16 |
| falling_into_place | 9 979 | 21 | 99.8% | ~33 |
| pass_the_parcel | 9 982 | 18 | 99.8% | ~29 |
| dive_bomb | 9 936 | 64 | 99.4% | ~80 |
| mind_the_gap | 9 938 | 62 | 99.4% | ~78 |
| keyhole | 9 914 | 86 | 99.1% | ~105 |
| the_funnel | 9 878 | 122 | 98.8% | ~145 |
| staircase | 9 697 | 303 | 97.0% | ~353 |

**Action**: one SLURM job using `--extend --target-valid 10000`.

---

### Needs extension — genuine impossibility, oracle confirmed correct

Seeds 0–9 999 exhausted. More seeds needed because a meaningful fraction
of seeds is genuinely impossible (not oracle failure). These levels were
confirmed by the 40×40 sweep study (2026-04-03).

| Level | Valid | Missing | Valid % | Confirmed impossible % | Extra seeds est. |
|---|---|---|---|---|---|
| pinball_machine | 8 714 | 1 286 | 87.1% | ~13% | ~1 673 |
| locust_swarm | 7 458 | 2 542 | 74.6% | ~25% | ~3 799 |
| the_cradle | 5 985 | 4 015 | 59.9% | ~40% | ~7 429 |

**Action**: one SLURM job per level using `--extend --target-valid 10000`.

Notes:
- **pinball_machine**: dense star configurations block all trajectories for
  ~13% of seeds. Oracle fix (5073bfc) confirmed 87.1% valid rate.
- **locust_swarm**: dense star chains block ~25% of seeds. Oracle fix (f51e781)
  confirmed 74.6% valid rate.
- **the_cradle**: V-cradle geometry resists top-down impact for ~40% of seeds.
  Oracle fix (0504e1e, top-down drop) confirmed 59.9% valid rate.

These are levels where 10 000 valid seeds require trying ~11 500 to ~17 000
total seeds. The genuine impossible seeds are expected; they represent hard
or structurally blocked configurations.

---

### Stale bundles — 1 k seeds, pre-fix oracle

Both bundles were generated before the oracle was corrected (commits ef5ed6b,
4e746df). Neither has been regenerated since. Valid counts are near-zero under
the old oracle.

#### catapult

| Metric | Value |
|---|---|
| Bundle seeds | 0–999 (1 000 total) |
| Valid seeds | 194 (19.4%) |
| oracle_commit in bundle | 8f3cee9 (pre-fix) |
| Oracle fix commit | ef5ed6b |
| Expected valid rate after fix | ~60% |
| Seeds needed for 10 000 valid | ~17 000 |
| Confirmed impossible % | ~40% |

Root cause of 40% genuine impossibility (per sweep study): basket/ledge geometry
where the launch trajectory never intersects the basket, regardless of red ball
placement. These seeds are structurally blocked.

**Action**: full regen with seeds 0:17000 and fixed oracle.

#### just_a_nudge

| Metric | Value |
|---|---|
| Bundle seeds | 0–999 (1 000 total) |
| Valid seeds | 1 (0.1%) |
| oracle_commit in bundle | 97f5549 (pre-fix) |
| Oracle fix commit | 4e746df |
| Expected valid rate after fix | ~10% |
| Seeds needed for 10 000 valid | ~100 000 |
| Confirmed impossible % | ~90% |

Root cause of 90% genuine impossibility (per sweep study): most seed geometries
have a platform/basket misalignment where the knocked green ball cannot reach
the basket regardless of red ball placement. The mechanism is direct knockoff,
not basket nudging. Only 3/30 swept seeds were solvable.

**Action**: regen seeds 0:10 000 to establish a baseline solvability number,
then flag for **level redesign review**. Generating 100 000 seeds for 10 000
valid is not appropriate before the design is fixed. The 10 000-seed bundle
(yielding ~1 000 valid) documents the true solvability rate under the current
design.

---

## Design flags for redesign review

After SLURM jobs complete, the following levels need design attention before
declaring the oracle pipeline done.

| Level | Issue | Severity |
|---|---|---|
| just_a_nudge | 90% genuine impossibility — basket/platform misalignment in most seeds | High — redesign required before 10 k valid is feasible |
| the_cradle | 40% genuine impossibility — V-cradle geometry blocks top-down drop | Medium — acceptable if intended difficulty; evaluate level intent |
| locust_swarm | 25% genuine impossibility — dense star chains block all paths | Low — within acceptable range for a hard level |
| pinball_machine | 13% genuine impossibility — dense star configurations | Low — acceptable |

---

## Oracle quality summary

All 23 levels with 10 k-seed bundles have confirmed oracles (oracle-sweep study
or near-100% valid rates indicate no systematic false negatives). Two stale bundles
(catapult, just_a_nudge) need regeneration with fixed oracles before their true
solvability rates can be measured.

No oracle improvements are needed before the SLURM jobs. The remaining oracle
work is the redesign of just_a_nudge and possibly the_cradle level geometry.

---

## Planned SLURM jobs

| Job | Levels | Type | Seeds | n_attempts | Est. wall time |
|---|---|---|---|---|---|
| bundle_topup | off_the_rails, straight_face, falling_into_place, pass_the_parcel, dive_bomb, mind_the_gap, keyhole, the_funnel, staircase | extend | auto | 50 | ~1 h |
| bundle_pinball | pinball_machine | extend | auto | 50 | ~2 h |
| bundle_locust | locust_swarm | extend | auto | 50 | ~3 h |
| bundle_cradle | the_cradle | extend | auto | 50 | ~4 h |
| bundle_catapult | catapult | full regen 0:17000 | 17 000 | 50 | ~3 h |
| bundle_just_a_nudge | just_a_nudge | full regen 0:10000 | 10 000 | 50 | ~3 h |
