# Interphyre Codebase — 7-Dimension Structured Analysis

Produced by: interphyre-76n.2 (codebase_audit / analysis)
Date: 2026-03-19
Source: scratch/codebase_audit/module_map.md + targeted reads of environment.py, interventions

---

## Dimension 1: API Design & Consistency

### 1.1 Naming & Structural Inconsistencies

**Three ways to access scene objects.** The codebase exposes object data through three
separate paths with different types and semantics:

- `env.objects` — a `@property` on `InterphyreEnv` returning the `level.objects` dict
  (maps `str → PhyreObject`, i.e., data objects at construction-time state).
- `engine.objects()` — a *method* (not property) on `Box2DEngine` also returning
  `level.objects`. Shadowed by the `engine.bodies` attribute which holds the live
  Box2D bodies.
- `engine.get_state()` — returns position data as Python tuples.
- `env._get_physics_state()` — returns position data as numpy arrays (used internally
  for observations).

No single public method returns a unified, live-state, name-keyed dict of object
positions and velocities. The asymmetry between `get_state()` (tuples) and
`_get_physics_state()` (numpy arrays) is undocumented and actively confuses type-based
dispatch.

**`from_level()` vs string constructor.** `InterphyreEnv.__init__` takes
`level_name: str`; `InterphyreEnv.from_level()` takes a `Level` object. The
`from_level()` factory at line 267 manually replicates the entire `__init__` body. Any
new attribute added to `__init__` must be added to `from_level()` separately — a
maintenance hazard that has already caused the `collect_data.py` bug (it passes
`level=level` as a kwarg to `__init__`, which takes `level_name`).

**Action contract ambiguity.** The action is described in docstrings as
`List[Tuple[float, float, float]]` but `quickstart.py` passes a bare tuple and it
works. `step()` accepts both, but the action space is defined as `Box(low=..., high=...,
shape=(n_action_objects * 3,))` — a flat numpy array, not a list of tuples. The user
must convert between formats manually, and the conversion is not documented.

**`intervention_context()` ergonomics.** The `InterventionContext.modify_success_condition()`
method (line 113) mutates `self._env._level.success_condition` directly and does not
register it with the `StateSnapshot`-based rollback. `auto_rollback=True` only restores
Box2D body positions. Python-level level attributes — including the success condition —
are not restored. This is a correctness hole: a `with intervention_context(auto_rollback=True)`
block that modifies the success condition and then raises an exception will leave the
environment with the modified condition.

**Naming collision: `run_until()` vs `step_until()`.** Both run the simulation until a
trigger fires. `run_until()` returns `(StateSnapshot | None, int)`. `step_until()`
returns Gym-style `(obs, reward, terminated, truncated, info)`. The distinction is not
surfaced in method names — both "run until" something. A more descriptive pair would be
`run_until_trigger()` and `step_until_trigger()`.

### 1.2 The `simulate()` Method

`env.simulate()` is a public method but does not call `_place_action_objects()`. It
steps physics forward from whatever the current world state is. This means it cannot be
used as a drop-in for running a full episode from scratch. Combined with the private
`_step_physics()` method (the only single-step interface), there is no clean public API
for "place the action object, then step one frame."

### 1.3 Bounds Hardcoding

`_is_within_bounds()` at line 1078 hardcodes `-5.0` and `5.0` rather than reading from
`config.MAX_X / MIN_X`. `SimulationConfig` already defines these constants; this is an
internal inconsistency that silently breaks if the world size is ever changed.

---

## Dimension 2: LLM Tool-Call Interface

### 2.1 Missing Scene Description

The most critical gap: **no function produces a natural-language or structured-text
description of the current scene state** that could serve as an LLM observation.

- `get_level_info()` returns `{name, action_objects, total_objects, object_types,
  metadata}`. It omits object positions, sizes, colors, and current physics state.
- `_get_physics_state()` is private and returns numpy arrays — not JSON-serializable.
- `env.objects` returns `PhyreObject` instances with no `__repr__`.

An LLM tool-calling Interphyre cannot learn "where is the green ball right now" via any
public method without custom wrapper code.

### 2.2 Contact Log Gated Behind Profiler

`get_contact_log()` and `get_contact_statistics()` are documented as research APIs.
They return empty results unless `enable_profiling=True` in `SimulationConfig`
(`interphyre/engine.py:94-103`). This is not documented anywhere in the API docs or
tool-call interface. An LLM tool using `get_contact_statistics()` silently receives zeros.

### 2.3 No Partial Simulation API

The LLM tool-call workflow requires: "place action → run N steps → query state → decide
on next action." Currently:

- `run_until(trigger, action=..., max_steps=N)` is the closest: it places the action and
  runs until a trigger fires (or N steps). But it returns a `StateSnapshot`, not a
  readable state dict. The LLM cannot read a `StateSnapshot`.
- `simulate(return_trace=True)` generates a step-by-step trace, but does not accept an
  action argument and does not call `_place_action_objects()`.
- `step()` runs for one entire "episode" (places action, runs to completion, returns
  terminal obs). There is no `step_one_frame()`.

The workaround used in `demos/counterfactuals.py` is to call `env._step_physics()`
directly — a private method. This is the only single-step public-equivalent path, and
it is private.

### 2.4 Return Values Are Not JSON-Serializable

- `_get_physics_state()` returns `np.ndarray` for position and velocity. Standard
  `json.dumps()` fails on numpy arrays.
- The contact matrix is an `(N, N)` boolean numpy array indexed by *positional index*
  into `object_names = list(self._level.objects.keys())`. An LLM receiving this matrix
  cannot determine which index corresponds to which named object without also knowing
  the key-order of the dict — fragile.
- `get_state()` on the engine returns Python tuples, which are JSON-serializable, but
  omits velocities and angles.

### 2.5 Functions That Should Be Exposed as Tools (But Aren't, Or Can't Be)

| Function | LLM-friendly? | Issue |
|---|---|---|
| `get_level_info()` | Partially | Missing positions, sizes, colors |
| `get_contact_log()` | No | Empty without profiler |
| `run_until(trigger, action)` | No | Returns StateSnapshot, not text |
| `env.objects` | No | PhyreObject has no __repr__ |
| `engine.get_state()` | Partially | Tuples only, no velocities |
| `simulate(return_trace=True)` | No | Doesn't accept action; numpy arrays |
| `env.success` | Yes | Boolean, clean |

### 2.6 No Text Scene Description for Level Setup

`Level` has no `describe()` or `to_text()` method. An LLM receiving the scene at
episode start cannot determine what objects exist, where they are, or what the success
condition is, purely from public API calls.

---

## Dimension 3: Level Architecture

### 3.1 No Enforced Level Contract

`Level.__post_init__` validates only that `success_condition` is callable. It does not
validate:

- That `action_objects` names exist as keys in `objects`.
- That action objects are `Ball` instances (the physics engine assumes this when placing
  them).
- That any required metadata keys are present.
- That objects don't overlap at construction time.

All 25 levels are tested by `test_all_levels.py` at runtime, so egregious errors are
caught, but structural invariants are not enforced at definition time.

### 3.2 Metadata Is Freeform

`level.metadata` is an untyped `dict`. In practice the only universal key is
`"description"` (a string). The `"action_bounds"` key is read by
`_setup_action_space()` in the environment — but if a level omits it, the fallback is
the full world bounds, which may include invalid placements. No schema, no
`TypedDict`, no validation.

### 3.3 Procedural Generation Robustness

**`down_to_earth.py`**: The action ball radius varies per seed (`rng.uniform(0.3, 0.6)`
at the same RNG call sequence as platform geometry). To independently control platform
position while holding action ball radius fixed, the level builder function must be
bypassed entirely — there is no parameter-level control. The ball x-position is
determined by platform geometry (centered above platform), so there is no independent
variation in ball x. These correlated RNG draws make controlled counterfactual dataset
generation impossible without monkey-patching.

**`catapult.py`**: Dynamic basket placed on a tilted ledge. The basket will slide or
fall under gravity before the action ball reaches it. The exact basket position at
contact time is not reproducible if the ledge tilt varies slightly across seeds.

**`bar.py` classmethods `ramp_to_wall()` and `touching_wall()`**: Compute lengths using
trigonometric division. When `wall_side="top"` or `"bottom"` with `angle=0`,
`math.sin(0) = 0` causes division by zero. These methods will crash on horizontal bars,
which is a common case.

**Unsolvable level detection**: There is no API-level check for whether a procedurally
generated scene is solvable. A platform that extends to both walls in `down_to_earth`
would make the level impossible — this is not detected at construction time.

### 3.4 Level Discoverability

`list_levels()` returns alphabetically sorted names. There is no API to query level
metadata (description, difficulty, action object types) without instantiating each
level. All 25 level modules are eagerly imported at `import interphyre`
(`interphyre/levels/__init__.py`), adding startup overhead even if only one level is
needed.

### 3.5 Action Object Placeholder Position Bug

The action object placeholder in `level.objects` is stored at position `(0, 0)` before
placement. The placement validation in `environment.py` checks whether the proposed
action collides with existing objects. If any scene object is near `(0, 0)`, the
validator may report a false collision.

---

## Dimension 4: Observation Space

### 4.1 What the Observation Contains

In `physics_state` mode, each step returns:
```python
{
    "objects": {
        "<name>": {
            "position": np.array([x, y]),     # float32
            "velocity": np.array([vx, vy]),    # float32
            "angle": float,
            "angular_velocity": float,
            "type": str,                        # "Ball", "Bar", "Basket"
        }
        ...
    },
    "contacts": np.ndarray,  # bool, shape (N, N)
    "step_count": int,
}
```

This is rich for RL but has several issues for research use:

**Contact matrix is positionally indexed.** The `(i, j)` entry corresponds to
`object_names[i]` and `object_names[j]`, where `object_names = list(level.objects.keys())`.
Dictionary key order is insertion order (Python 3.7+), which is stable within a run but
varies across levels and seeds if objects are added conditionally. An LLM or probe model
receiving this matrix must separately know the key order.

**No contact duration or normal direction.** The contact matrix says whether two objects
are in contact but not for how long or with what geometry. Most success conditions use
duration-gated contact — the observation doesn't directly expose the durational
information needed to predict success.

**No velocity history.** A single step's observation contains current velocity but no
history. Sequence models for probing or DAS need step-indexed state histories. The
`simulate(return_trace=True)` method exists but is disconnected from the intervention
workflow (it doesn't place action objects).

**No contact log in observation.** `get_contact_log()` and `get_contact_statistics()`
exist as separate methods but are not part of the returned observation. They return empty
results by default (profiler gate). Including contact history in the observation, or
making the contact log always available, would be valuable for interpretability
experiments.

### 4.2 Object Identity Stability

Within a fixed `(level_name, seed)` pair, object names are stable. Across seeds, the
names are stable (level builders hardcode names like `"green_ball"`, `"platform"`).
This means probe models trained on one seed's observations can be applied to others.
However, the contact matrix is positionally indexed, so if two different levels have
different object counts, the observation shapes differ — no unified representation across
levels.

### 4.3 Velocity Bounds in Observation Space

`observation_space` for velocity is `Box(low=-10, high=10)`. The actual Box2D physics
can produce velocities exceeding ±10 m/s for dynamic objects under sustained force. A
ball falling from the top of the world (y=5) under gravity ≈ 9.8 m/s² reaches ≈13 m/s
by the time it hits the bottom. The observation space bounds are too narrow, producing
invalid observations that violate the Gymnasium spec during fast dynamics.

---

## Dimension 5: Determinism & Reproducibility

### 5.1 Seeding Inconsistency at Initialization

`InterphyreEnv.__init__` calls `self.reset()` at line 242 before the caller can supply a
seed. At this point, `self.np_random` is set via `np.random.default_rng()` with no
seed. When the user subsequently calls `env.reset(seed=N)`, `np_random` is overridden —
but the initial `reset()` has already consumed some state (e.g., it may have placed the
action object placeholder). The level builder uses its own `rng` initialized from the
seed passed to `load_level(name, seed)`, which is separate from `env.np_random`. The
compound effect: `env.np_random` and the level's `rng` are two separate RNG streams
with independent state, and only the level's `rng` is seeded at construction.

### 5.2 Box2D Physics Determinism

Box2D is deterministic for a given sequence of inputs on the same platform. However:

- `PerformanceProfiler` uses `time.perf_counter()` (wall clock). This is non-deterministic
  but doesn't affect physics.
- `world_is_stationary()` uses a velocity history list with `pop(0)` (O(N) per step due
  to list shifting). This doesn't affect correctness but introduces unnecessary overhead.
- There is no documented guarantee of cross-platform (x86 vs ARM) floating-point
  reproducibility. Box2D uses IEEE 754 arithmetic but does not pin FPU mode.

### 5.3 StateSnapshot Reproducibility

`StateSnapshot` is the primary reproducibility mechanism. Issues:

- Uses `pickle` for serialization (lines 165, 192). Pickle is not version-safe — a
  snapshot saved with Box2D 2.3.x may not restore correctly after a library update.
- `_hash_level()` hashes `(name, type, x, y, angle)` but not shape dimensions. Two scenes
  with the same object names and positions but different ball radii produce the same hash.
  A restore that silently succeeds on the wrong level geometry is worse than a failed
  restore.
- `step_index` is computed from `contact_listener.current_time / config.time_step`
  (floating-point division). Off-by-one drift possible vs. `env.step_count`.

### 5.4 Scene Reproduction From (level_name, seed, action)

In principle, a `(level_name, seed, action)` triple should fully determine a trajectory:

```python
env = InterphyreEnv("down_to_earth", seed=42)
env.reset(seed=42)
obs, *_ = env.step(action)
```

In practice, `__init__` calls `reset()` once before the user's `reset(seed=42)`, and
`env.np_random` is seeded twice. For levels whose `build_level()` doesn't consume
`env.np_random` (they use their own `rng`), this is harmless. But for any future level
that reads from `env.np_random` during reset, the double-reset would produce a
different scene than expected.

---

## Dimension 6: Interpretability Research Support

### 6.1 Dataset Generation: Critical Bug in collect_data.py

`DataCollector._create_env()` (line 370) and `_verify_action()` (line 483) both call
`InterphyreEnv(level=level, config=self.config, ...)`. The first positional argument of
`InterphyreEnv.__init__` is `level_name: str`. Passing `level=level` (a `Level` object)
as a keyword raises `TypeError`. The data collection pipeline is non-functional as
written. The correct call is `InterphyreEnv.from_level(level, config=self.config, ...)`.

This is the single highest-severity bug in the codebase from the research perspective: the
primary tool for generating `(scene, action, outcome)` datasets crashes before producing any data.

### 6.2 Counterfactual Pair Generation

Generating counterfactual pairs — two scenes differing in exactly one variable — requires
independent control of:

- Platform x, y, width (for `down_to_earth`)
- Green ball initial position (currently determined by platform geometry)
- Red action ball radius (currently entangled with platform RNG draw sequence)
- Red action ball placement (action space, independent of level builder)

None of these can be controlled independently via the current `load_level(name, seed)`
API. The only lever is the seed, which co-varies all of the above.

**Workaround complexity**: To fix platform_x while varying platform_width, one would
need to:
1. Copy the `down_to_earth.build_level` function body
2. Replace the `rng.uniform(...)` calls with fixed values
3. Reconstruct the `Level` object manually
4. Call `env.from_level(level)`

There is no supported "parameterized level builder" interface. This is P0 friction for
interpretability research on `down_to_earth`.

### 6.3 Trajectory History for Probing and DAS

For sequence model probing or DAS counterfactual analysis, a per-step state history is
needed. `simulate(return_trace=True)` produces this:
```python
trace = env.simulate(steps=240, return_trace=True)
# trace[i] = (obs_i, reward_i, done_i, truncated_i, info_i)
```
But `simulate()` does not accept an `action` argument and does not call
`_place_action_objects()`. The workaround is to manually call `_place_action_objects()`
(private), then `simulate()`. There is no public-facing "simulate episode from action,
return full trajectory" method.

### 6.4 Single-Step Physics for Causal Tracing

Causal tracing requires running forward to a specific step T, querying state, then
branching. The `run_until(at_step(T))` API supports this. However:

- `at_step(T)` fires when `step_index + 1 == T`. After `run_until()`, the snapshot
  captures body states. No object velocity or contact history is included in the
  snapshot's readable metadata.
- There is no `env.get_state_at_step(T)` that returns a fully named, JSON-serializable
  dict. The returned `StateSnapshot` can only be used to call `restore()` — it is not
  a readable data structure.

### 6.5 Do-Calculus Interventions

The intervention API supports `set_position()`, `set_velocity()`, `freeze()`, and
`apply_impulse()`. These are the right primitives for do-calculus interventions.
Caveats:

- `set_position()` sets body position directly via Box2D `body.position = (x, y)`. If
  the body has nonzero velocity when its position is set, it retains that velocity.
  No automatic velocity zeroing. This is physically correct (a "teleport" intervention
  retains momentum) but may not be the intended semantics for interpretability
  experiments where the intervention should mean "object was at position X at time T,
  not at its actual position."
- `InterventionContext.modify_success_condition()` does not participate in rollback.
  Replacing the success condition inside a `with intervention_context(auto_rollback=True)`
  block will permanently alter the level even if an exception is raised.

### 6.6 Level Controllability for `down_to_earth`

The plan identifies `down_to_earth` as the primary research level. The controllability
issue is severe:

- **Platform position**: driven by `rng.uniform`. No public parameter.
- **Ball position**: `platform_x + platform_width/2` — fully determined by platform.
- **Ball radius**: `rng.uniform(0.3, 0.6)` in the same RNG sequence. Cannot be
  independently fixed.
- **Action ball radius**: `rng.uniform(0.3, 0.6)` for `red_ball_radius`. Same sequence.
- **Platform width**: `rng.uniform(1, 7)`. No independent control.

All five variables are entangled in a single forward RNG sequence. The only supported
access point is `seed`.

---

## Dimension 7: Documentation & Developer Experience

### 7.1 LLM Tool-Call Workflow: Zero Coverage

The primary research use case — an LLM calling Interphyre as a tool API — has no
documentation in `docs/`. There is no page covering:

- What functions to expose as LLM tools
- The expected input/output schema for each tool
- How to convert numpy observations to text
- How to use `run_until()` for partial simulation
- How to generate counterfactual dataset pairs

This is the most significant documentation gap.

### 7.2 Stale and Misleading Docstrings

- `SimulationConfig`: docstring states `velocity_iters=6` and `position_iters=2`. Code
  defaults are 15 and 20 respectively (`config.py`).
- `enable_interventions` flag docstring implies trigger evaluation is skipped when
  `False`. Actually, triggers evaluate on every step regardless; only snapshot allocation
  is skipped.
- `docs/api/environment.md` does not document that `get_contact_log()` returns empty
  unless `enable_profiling=True`.

### 7.3 Private Method Exposure in Demos

`demos/counterfactuals.py` calls `env._step_physics()` (private). The reason: there is
no public single-step method. This is documented nowhere. A user reading the demo and
trying to follow the pattern in their own code will reach for a private method.

### 7.4 `docs/getting-started.md`

The "Running Demos" command `for f in demos/*.py; do python $f; done` opens multiple
pygame windows sequentially without cleanup. Levels with `render_mode="human"` will hang
waiting for window close.

### 7.5 `setup.py` Package Exclusions

`agents/` is excluded from the installable package. `tools/collect_data.py` uses a
`sys.path.insert` workaround to import from `agents`. This means research code that
depends on `agents` cannot be installed cleanly via pip — it works only when run from the
repo root.

### 7.6 API Reference Coverage

The `docs/api/` folder covers environment, level, engine, config, interventions, objects,
and render. Coverage is reasonable. Missing:

- Document `enable_profiling` requirement for contact log methods.
- Document the `from_level()` vs string-constructor distinction and maintenance hazard.
- Document the `observation_type` parameter and the shape of each observation mode.
- Document `simulate(return_trace=True)` as the trajectory-trace method and its
  limitation (no action placement).

---

## Summary of Critical Findings by Severity

| Finding | Location | Severity |
|---|---|---|
| `collect_data.py` crashes: `level=` kwarg to `InterphyreEnv` | `tools/collect_data.py:370,483` | Bug / P0 |
| No scene description method (text or structured dict) | `interphyre/level.py`, `environment.py` | P0 Gap |
| `get_contact_log()` empty by default (profiler gate undocumented) | `engine.py:94-103` | P0 Gap |
| Correlated RNG in `down_to_earth` — no independent variable control | `levels/down_to_earth.py` | P0 Research Gap |
| No public single-step method (`_step_physics` is private) | `environment.py` | P0 Gap |
| `_distance_ball_to_bar` uses initial bar state, not current physics | `engine.py:638` | Bug / P1 |
| `StateSnapshot` hashes exclude shape dimensions | `interventions/state.py:348` | Bug / P1 |
| `StateSnapshot` uses `pickle` — not version-safe | `interventions/state.py:165` | P1 |
| Contact matrix is positionally indexed — not name-keyed | `environment.py:1229` | P1 |
| Observation velocity bounds `(-10, 10)` too narrow | `environment.py:727` | P1 |
| `InterventionContext` rollback doesn't cover success condition mutation | `environment.py:113` | P1 |
| Dual `__init__` / `from_level()` paths — maintenance hazard | `environment.py:267` | P1 |
| No trajectory trace from action → full episode via public API | `environment.py:1291` | P1 |
| No LLM tool-call documentation | `docs/` | P1 |
| `_active_interventions` populated but never consumed (dead code) | `environment.py:862` | P2 |
| `segmented_walls` dead code in `create_basket` | `objects/basket.py:79` | P2 |
| `RandomAgent.rng` never used | `agents/random_agent.py:45` | P2 |
| Stale `SimulationConfig` docstring (`velocity_iters`, `position_iters`) | `config.py` | P2 |
| `world_is_stationary()` uses list.pop(0) — O(N) per step | `engine.py:556` | P2 |
| `bar.ramp_to_wall()` divides by zero for horizontal bars | `objects/bar.py` | P2 |
