# Smoke Test Summary: `interphyre/validation/` Module

Task: `interphyre-u9g.12`
Date: 2026-03-26

---

## Per-Level Seed Coverage (seeds 0–99, max_variants=10)

| Level | Seeds tested | Valid (v=0) | Required variant > 0 | Invalid (exhausted) | Exhaustion % |
|---|---|---|---|---|---|
| basket_case | 100 | 31 | 69 | 0 | 0.0% |
| tipping_point | 100 | 93 | 7 | 0 | 0.0% |
| straight_face | 100 | 53 | 47 | 0 | 0.0% |

**Notes:**
- "Valid (v=0)" = seeds where variant 0 passed the trivial and oracle checks.
- "Required variant > 0" = seeds where variant 0 was invalid (trivial or oracle fail) but a later variant succeeded. These seeds are still fully usable — the variant system resolves them transparently.
- "Invalid (exhausted)" = seeds where all 10 variants were tried without finding a valid level. A value of 0 means every seed in this range has a usable geometry.
- basket_case shows the highest variant demand (69% of seeds needed v > 0), consistent with its oracle being more sensitive to geometry — a targeted oracle exists and is necessary.
- tipping_point is the most stable level: 93% of seeds are valid at v=0.

---

## Quantitative Success Criteria

| Criterion | Target | Result | Status |
|---|---|---|---|
| All 27 unit tests pass | 27/27 | 27/27 (0.66s) | **PASS** |
| Exhaustion < 10% per level | < 10% | 0.0% for all three | **PASS** |
| No valid scene dict satisfies `is_trivial` | 0 violations | 0 violations (100 valid scenes checked per level) | **PASS** |
| Scene dict round-trip fidelity | 0 mismatches | 0 mismatches | **PASS** |

---

## Unit Test Results (tests/test_validation.py — 19 tests)

| Test | Status |
|---|---|
| test_is_trivial_false | PASS |
| test_is_trivial_true | PASS |
| test_variant_zero_backward_compat | PASS |
| test_variant_nonzero_distinct | PASS |
| test_oracle_finds_solution | PASS |
| test_list_oracles_coverage | PASS |
| test_registry_roundtrip | PASS |
| test_registry_idempotent | PASS |
| test_validate_level_caches | PASS |
| test_load_valid_level_returns_validated_level | PASS |
| test_load_valid_level_variant_increment | PASS |
| test_iter_valid_levels | PASS |
| test_scene_dict_round_trip | PASS |
| test_bundled_lookup | PASS |
| test_bundled_scene_reconstruction | PASS |
| test_default_registry | PASS |
| test_schema_hash_stored | PASS |
| test_schema_hash_valid | PASS |
| test_schema_hash_stale | PASS |

## Unit Test Results (tests/test_env_validation.py — 8 tests)

| Test | Status |
|---|---|
| test_env_default_validate_true | PASS |
| test_env_variant_accessible | PASS |
| test_env_validate_false_no_scene_dict | PASS |
| test_env_trivial_seed_produces_valid_level | PASS |
| test_env_provenance_loggable | PASS |
| test_env_custom_level_object_trivial_warns | PASS |
| test_env_custom_level_object_scene_dict_populated | PASS |
| test_env_custom_registered_level_full_pipeline | PASS |

**Total: 27/27 passed in 0.66s**

---

## Bundle Coverage (context from bundle generation, seeds 0–999)

| Level | Valid seeds | Trivial | Total impossible entries |
|---|---|---|---|
| basket_case | 989/1000 | 0 | 1695 |
| tipping_point | 1000/1000 | 0 | 109 |
| straight_face | 999/1000 | 0 | 924 |

The 1 exhausted seed in `straight_face` is outside the smoke test range (seeds 0–99 all resolved). No level produced any trivial entries — the `is_trivial` check fired zero times across all three levels over 1000 seeds, indicating these level templates do not produce t=0 success configurations.
