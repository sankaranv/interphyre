# Interphyre v0.0.2 Repair Summary

| # | Proposal | Priority | Status | Regression Test | Commit SHA |
|---|----------|----------|--------|-----------------|------------|
| 1 | FIX-COLLECT-DATA + UNIFY-INIT-FROM-LEVEL | P0 | fixed | `InterphyreEnv(level=Level(...))` and `InterphyreEnv("down_to_earth")` both succeed; collect_data.py `_create_env`/`_verify_action` corrected | `d7fafd3` |
| 2 | ADD-SCENE-DESCRIPTION | P0 | fixed | `json.dumps(env.describe_scene())` passes all 25 levels; values match `engine.get_state()` and `_get_physics_state()` | `cac8f67` |
| 3 | FIX-CONTACT-LOG-GATE | P0 | fixed | `get_contact_log()` returns 8 events with default `SimulationConfig()` (no profiling flag) | `3020fa4` |
| 4 | ADD-PARAMETERIZED-LEVEL-BUILDER | P0 | fixed (redesigned) | `build_level(42)` bit-identical before/after; `build_level(42, platform_width=3.0)` preserves RNG for other vars; scene-based fixture round-trip passes | `2bf275e` + `dc4b826` + `132f1d2` + `04e9baf` |
| 5 | EXPOSE-STEP-PHYSICS-AND-PLACE-ACTION | P0 | fixed | `demos/counterfactuals.py` runs without calling any private methods | `510e4e7` |
| 6 | FIX-SNAPSHOT-HASH | P1 | fixed | Two levels with same names/positions but different radii produce different hashes; `restore()` raises on cross-scene mismatch | `9b5803d` |
| 7 | FIX-ENGINE-BAR-CONTACT-DISTANCE | P1 | fixed | Bar drifted 3.7 units and 107° in catapult; old code error 3.32 units, fixed error 0.000 | `b0942b8` |
| 8 | FIX-RELEVANT-CONTACTS-COLOR-HEURISTIC | P1 | fixed | `blue_ball↔basket` contact confirmed in catapult regression (4 events); all non-green pairs now tracked | `febd874` |
| 9 | FIX-VELOCITY-OBSERVATION-BOUNDS | P1 | fixed | 25 levels × 240 steps, 0 bound violations with new (−50, 50) m/s limits | `3c2fff8` |
| 10 | FIX-ROLLBACK-SUCCESS-CONDITION | P1 | fixed | `modify_success_condition` inside `intervention_context(auto_rollback=True)` raises; original condition restored | `780ca97` |
| 11 | ADD-CONTACT-DURATION-TRIGGER | P1 | fixed | `on_contact_duration('green_ball', 'purple_ground', 0.5)` fires at step 526 for down_to_earth (seed=42) | `7db8b42` |
| 12 | FIX-CONFIG-DOCSTRING | P2 | fixed | Docstring updated: `velocity_iters` 6→15, `position_iters` 2→20; `enable_interventions` semantics clarified | `4cb1e44` |
| 13 | REMOVE-DEAD-CODE | P2 | fixed | `segmented_walls` removed from Basket; `_active_interventions` removed from InterphyreEnv; `RandomAgent.set_seed()` seeds `action_space` | `22bb8aa` |
| 14 | FIX-BOUNDS-HARDCODING | P2 | fixed | `_is_within_bounds()` uses `MIN_X/MAX_X/MIN_Y/MAX_Y` from config; hardcoded ±5.0 removed | `e67365a` |

**Final count: 14/14 accepted proposals closed.**

## Notes on Proposal 4 (ADD-PARAMETERIZED-LEVEL-BUILDER)

The original plan proposed a typed `DownToEarthParams` dataclass. During implementation, this was redesigned into three commits:

- `2bf275e` (interphyre-t1y.5): Added `DownToEarthParams` dataclass and draw-then-override `build_level()`.
- `dc4b826` (interphyre-t1y.17): Replaced `DownToEarthParams` with a uniform `**overrides` dict convention so that `load_level('down_to_earth', seed=42, platform_width=3.0)` works for all 25 levels without per-level imports.
- `132f1d2` (interphyre-s2w): Added `build_level_from_scene()` entry point for fully geometry-specified scenes (no RNG).
- `04e9baf` (interphyre-0he): Migrated `tests/solutions/successes.json` from seed-based to scene-based format; `test_solution_validation.py` now uses `build_level_from_scene()`.

The redesign supersedes the plan's `DownToEarthParams` proposal but satisfies the same regression criteria: independent variable control with preserved RNG sequence.

## Pre-existing failures (not introduced by repairs)

The following tests failed both at baseline and at close; none were introduced by the repairs:

- `tests/test_engine.py::test_contact_distance_ball_ball_invalidates_contact` — pre-existing
- `tests/test_engine.py::test_contact_distance_ball_bar_invalidates_contact` — pre-existing
- `tests/test_engine.py::test_contact_distance_bar_ball_invalidates_contact` — pre-existing
- `tests/test_performance.py::test_configuration_system_defaults` — asserts `velocity_iters == 6` and `gravity == (0, -10)`; both wrong relative to code; the test was written against stale documentation. FIX-CONFIG-DOCSTRING fixed the docstring but this test itself contains incorrect expected values.
- `tests/test_renderers.py::test_pygame_wait_calls_time_wait` — pygame mock incompatibility, pre-existing.
- `tests/test_solution_validation.py::test_success_solutions_succeed[two_body_problem-{0..9}]` — 10 two_body_problem scene fixture failures, reduced from 11 at baseline after MIGRATE-SOLUTION-FIXTURES-TO-SCENE-BASED.
