# api_hardening — Experiment Summary

## Hypothesis

From the plan's advisor sentence: "After applying the v0.0.4 hardening, the core
intervention primitives (`step_physics`, `place_action`, `step_until`, `add_object`,
`remove_object`) have dedicated integration tests, object state is accessible without
reaching into Box2D internals, and contact log keys are deterministic across runs."

## Setup and Execution

Seven proposals were identified during post-repair review of the v0.0.3 branch, targeting
test coverage (P1), API surface (P1), code hygiene (P2), and documentation/type hints (P3).
Each proposal was implemented as an atomic commit on the `refactor/codebase_audit` branch.

Tasks were tracked via beads epic `interphyre-35k` with 7 implementation tasks plus this
output task. All implementation tasks had explicit regression test commands verified before
closing.

## Result

**7/7 proposals fixed** with passing regression tests.

- **P1 — Test coverage**: 12 new integration tests covering `step_physics`, `place_action`,
  `step_until`, `add_object`, and `remove_object` (happy-path and boundary cases).
- **P1 — Public API**: `validate_action()`, `get_object_position()`, and `get_object_state()`
  exposed as public methods; downstream callers updated.
- **P2 — Dead code**: `contact_duration` and `all_contacts_log` removed from
  `GoalContactListener`.
- **P2 — Ergonomics**: `__repr__` added to `PhyreObject` and subclasses.
- **P2 — Determinism**: Contact pair keys now sorted alphabetically.
- **P3 — Documentation**: Wall exclusion in `_validate_contact_distances()` documented.
- **P3 — Type hints**: `success_condition` typed as `Callable[[Box2DEngine], bool]`.

See [hardening_summary.md](hardening_summary.md) for the per-proposal table with commit SHAs.

## Consistency with Hypothesis

**Consistent.** All three claims in the advisor sentence are satisfied:
1. Core intervention primitives have dedicated integration tests (TEST-CORE-PRIMITIVES).
2. Object state is accessible via public API without Box2D internals (EXPOSE-VALIDATE-ACTION).
3. Contact log keys are deterministic across runs (SORT-CONTACT-PAIR-KEYS).

## Deviations from Plan

- FIX-SUCCESS-CONDITION-TYPEHINT: Used `from __future__ import annotations` with
  `TYPE_CHECKING` guard to avoid a circular import between `level.py` and `engine.py`.
  The plan did not anticipate this, but the approach is standard and `ruff check` passes.
- No proposals were skipped.
