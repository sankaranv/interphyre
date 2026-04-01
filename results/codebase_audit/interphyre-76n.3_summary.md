# Codebase Audit Summary

**Task**: interphyre-76n.3 (codebase_audit / output)
**Date**: 2026-03-19
**Artifact**: results/codebase_audit/interphyre-76n.3_report.md

---

## Hypothesis

> Verify or falsify: this codebase has critical gaps preventing research-grade use for LLM
> mechanistic interpretability experiments.

**Verdict: VERIFIED.** The codebase has five distinct P0 gaps that, individually or in
combination, block the primary research workflow. The most severe is a `TypeError` crash
in `tools/collect_data.py` that makes the dataset generation pipeline non-functional before
producing a single data point.

---

## Experimental Setup

This audit was conducted in three sessions (tasks interphyre-76n.1 through interphyre-76n.3):

1. **Scan** (interphyre-76n.1): All source modules, docs, tests, and configuration files
   were read systematically. Findings were recorded in `scratch/codebase_audit/module_map.md`.

2. **Analysis** (interphyre-76n.2): The findings were organized across 7 dimensions defined
   in the plan (API Design, LLM Interface, Level Architecture, Observation Space,
   Determinism, Interpretability Support, Documentation). Results saved in
   `scratch/codebase_audit/dimension_analysis.md`.

3. **Output** (interphyre-76n.3): The module map and dimension analysis were synthesized
   into the final report at `results/codebase_audit/interphyre-76n.3_report.md`, including
   tiered improvement proposals and cross-cutting observations.

---

## Key Results

### P0 Issues (Blocks Research): 4 bugs + 1 structural gap

| ID | Issue | Location |
|---|---|---|
| FIX-COLLECT-DATA | `InterphyreEnv(level=level)` raises `TypeError` — pipeline non-functional | `tools/collect_data.py:370,483` |
| ADD-SCENE-DESCRIPTION | No public JSON-serializable scene state method | `interphyre/level.py`, `environment.py` |
| FIX-CONTACT-LOG-GATE | `get_contact_log()` empty by default (undocumented profiler gate) | `engine.py:94-103` |
| ADD-PARAMETERIZED-LEVEL-BUILDER | All 5 scene variables in `down_to_earth` entangled in single RNG stream — no independent control | `levels/down_to_earth.py` |
| ADD-PUBLIC-STEP-ONE-FRAME | Only single-step method is private (`_step_physics`) | `environment.py` |

### P1 Issues (Significant Friction): 9 items

Includes `StateSnapshot` hash excludes shape dimensions (silent restore on wrong scene),
pickle serialization not version-safe, contact matrix positionally indexed, velocity bounds
too narrow (observation space violation), missing contact-duration trigger, rollback does
not cover success condition mutation, no public trajectory API, `_distance_ball_to_bar`
uses initial bar state for dynamic bars, and color-heuristic contact relevance detection.

### P2 Issues (Quality): 7 items

Stale `SimulationConfig` docstring, three dead code items (including `RandomAgent.rng`
making `set_seed()` ineffective), hardcoded world bounds, bar division-by-zero, O(N)
velocity history, freeform level metadata, and `agents/` excluded from pip package.

---

## Interpretation vs. Hypothesis

The hypothesis is confirmed. The codebase is not research-grade in its current state:

- **Dataset generation**: `collect_data.py` crashes on every invocation — zero data can be
  produced via the supported API.
- **LLM tool-call**: No function returns a JSON-serializable scene description. Contact log
  is always empty unless a non-default profiler flag is set.
- **Counterfactual pairs**: All scene variables in the primary research level
  (`down_to_earth`) are entangled in one RNG stream. Independent variation of any single
  variable requires bypassing the API.

The codebase has a solid foundation: the intervention system is well-designed, the trigger
hierarchy is expressive, Box2D integration is stable, and the Gymnasium API is
well-structured for RL use. The gaps are concentrated at the research-tool interface layer,
not in the physics engine or core data model. All P0 items are surgical fixes (S or M
effort); none require architectural overhaul.

---

## Implementation Decisions Deviating from Plan

None. The plan called for a static analysis audit only (no code changes). All findings are
from source reading; runtime behaviors noted as "requires runtime verification" were not
experimentally confirmed.
