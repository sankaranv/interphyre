# Interphyre v0.0.4 API Hardening — Summary Table

| # | Proposal | Priority | Status | Regression Test | Commit |
|---|----------|----------|--------|-----------------|--------|
| 1 | TEST-CORE-PRIMITIVES | P1 | fixed | `pytest tests/test_intervention_primitives.py` | `e2351c4` |
| 2 | EXPOSE-VALIDATE-ACTION | P1 | fixed | `pytest -k "validate_action or get_object_position"` | `8d08b36` |
| 3 | CLEAN-DEAD-CONTACT-FIELDS | P2 | fixed | `pytest tests/ -x` | `2618d6f` |
| 4 | ADD-PHYREOBJECT-REPR | P2 | fixed | `pytest -k "repr"` | `328dc74` |
| 5 | SORT-CONTACT-PAIR-KEYS | P2 | fixed | `pytest -k "contact"` | `9c2feeb` |
| 6 | DOCUMENT-WALL-EXCLUSION | P3 | fixed | `ruff check interphyre/engine.py` | `2b65fa3` |
| 7 | FIX-SUCCESS-CONDITION-TYPEHINT | P3 | fixed | `ruff check interphyre/level.py` | `ad71177` |

**Result**: 7/7 proposals fixed with passing regression tests.
