# Smoke Test: All 25 Levels — Seeds 0–99

**Date**: 2026-03-27
**Study**: validation_repair
**Task**: interphyre-zoh.4

## Configuration

| Parameter     | Value |
|---------------|-------|
| Seeds tested  | 0–99 (100 seeds per level) |
| max_variants  | 10 |
| n_attempts    | 50 |
| oracle_steps  | 500 |
| is_trivial physics_steps | 1000 |
| Workers       | 8 |

**Note**: The 8 redesigned levels (catapult, falling_into_place, just_a_nudge, keyhole,
marble_race, mind_the_gap, the_cradle, wedge_issue) were tested using the live oracle
(stale Mar-25 bundles disabled). All other 17 levels used bundled data for O(1) lookups.

---

## Results Table

| Level | Seeds tested | Valid | Required variants >0 | Impossible | Exhausted | Exh% | Pass |
|---|---|---|---|---|---|---|---|
| basket_case | 100 | 100 | 0 | 0 | 0 | 0.0% | ✓ |
| catapult | 100 | 20 | 0 | 80 | 0 | 0.0% | ✓ |
| cliffhanger | 100 | 100 | 0 | 0 | 0 | 0.0% | ✓ |
| dive_bomb | 100 | 100 | 0 | 0 | 0 | 0.0% | ✓ |
| down_to_earth | 100 | 100 | 0 | 0 | 0 | 0.0% | ✓ |
| end_of_line | 100 | 100 | 0 | 0 | 0 | 0.0% | ✓ |
| falling_into_place | 100 | 87 | 0 | 13 | 0 | 0.0% | ✓ |
| flagpole_sitta | 100 | 100 | 0 | 0 | 0 | 0.0% | ✓ |
| just_a_nudge | 100 | 0 | 0 | 100 | 0 | 0.0% | ✓ (see note) |
| keyhole | 100 | 100 | 0 | 0 | 0 | 0.0% | ✓ |
| locust_swarm | 100 | 92 | 0 | 8 | 0 | 0.0% | ✓ |
| marble_race | 100 | 100 | 0 | 0 | 0 | 0.0% | ✓ |
| mind_the_gap | 100 | 30 | 0 | 70 | 0 | 0.0% | ✓ |
| off_the_rails | 100 | 99 | 0 | 1 | 0 | 0.0% | ✓ |
| pass_the_parcel | 100 | 100 | 0 | 0 | 0 | 0.0% | ✓ |
| pinball_machine | 100 | 89 | 0 | 11 | 0 | 0.0% | ✓ |
| seesaw | 100 | 100 | 0 | 0 | 0 | 0.0% | ✓ |
| staircase | 100 | 100 | 0 | 0 | 0 | 0.0% | ✓ |
| straight_face | 100 | 100 | 0 | 0 | 0 | 0.0% | ✓ |
| the_cradle | 100 | 0 | 0 | 100 | 0 | 0.0% | ✓ (see note) |
| the_funnel | 100 | 100 | 0 | 0 | 0 | 0.0% | ✓ |
| tipping_point | 100 | 100 | 0 | 0 | 0 | 0.0% | ✓ |
| two_body_problem | 100 | 100 | 0 | 0 | 0 | 0.0% | ✓ |
| wedge_issue | 100 | 100 | 0 | 0 | 0 | 0.0% | ✓ |
| zebra_crossing | 100 | 97 | 0 | 3 | 0 | 0.0% | ✓ |

**Summary**: 25/25 levels pass the exhaustion criterion (<10% exhausted).
**Exhausted seeds**: 0 across all 25 levels (0%).

---

## Unit Test Results

```
tests/test_validation.py — 30 passed, 2 skipped in 1.10s

PASSED (30):
  test_is_trivial_false
  test_is_trivial_true
  test_variant_zero_backward_compat
  test_variant_nonzero_distinct
  test_oracle_finds_solution
  test_list_oracles_coverage
  test_registry_roundtrip
  test_registry_idempotent
  test_validate_level_caches
  test_load_valid_level_returns_validated_level
  test_load_valid_level_variant_increment
  test_iter_valid_levels
  test_scene_dict_round_trip
  test_bundled_lookup
  test_bundled_scene_reconstruction
  test_default_registry
  test_schema_hash_stored
  test_schema_hash_valid
  test_schema_hash_stale
  test_is_trivial_extended_false              [NEW — A4]
  test_is_trivial_extended_physics_only       [NEW — A4]
  test_oracle_rng_bundle_live_match           [NEW — A1]
  test_iter_valid_levels_skips_exhausted      [NEW — A2]
  test_registry_db_path_public               [NEW — A3]
  test_catapult_oracle_finds_solution         [NEW — B3]
  test_mind_the_gap_oracle_finds_solution     [NEW — B4]
  test_marble_race_oracle_finds_solution      [NEW — B5]
  test_keyhole_oracle_finds_solution          [NEW — B6]
  test_falling_into_place_oracle_finds_solution [NEW — B7]
  test_wedge_issue_oracle_finds_solution      [NEW — B8]

SKIPPED (2):
  test_the_cradle_oracle_finds_solution       [NEW — B1, SKIP]
  test_just_a_nudge_oracle_finds_solution     [NEW — B2, SKIP]
```

---

## Notes

### just_a_nudge and the_cradle: 0% valid, 0% exhausted

Both levels show 100% impossible for seeds 0–99 under the new valid-placement oracle.
The exhaustion criterion (<10% exhausted) is met — no seeds exhaust all 10 variants —
because the oracle quickly classifies each seed as "impossible" (all 50 attempts in
variant 0 fail and all 10 variants are consistently impossible).

Detailed investigation in `scratch/validation_repair/interphyre-zoh.13_investigation.txt`
confirms both levels are genuinely unsolvable with valid (non-overlapping) placements:

- **the_cradle**: Near-tangent lateral push creates insufficient lateral force to overcome
  the 5° V-cradle restoration force. Valid zone for holder-drop placement is empty for
  most seeds (bar too short). Dense grid (1517 valid positions, 2000 oracle steps): 0 solutions.

- **just_a_nudge**: Basket displacement required (0.7–2.1 units) is 10–14× larger than
  what a valid ball drop can produce (0.05–0.15 units). Natural trajectory never lands
  within 0.7 units of the basket (minimum gap: 0.74 units, seed=2).

These levels previously relied on Box2D position-correction impulses (overlap placement),
which are forbidden by `_is_valid_oracle_placement`. Redesign of the level geometry (not
the oracle) would be required to make them solvable with valid placements.

**23/25 levels are fully operational** (all meeting <10% exhaustion AND having >0% valid seeds).

### pinball_machine: 11% impossible, 0% exhausted

pinball_machine has 11 impossible seeds in 0–99. The primary criterion (exhaustion < 10%)
is met (0.0%). Monitor only — does not require oracle redesign.
