# Interphyre Codebase Audit: v0.0.2 Improvement Proposal

**Task**: interphyre-76n.3
**Date**: 2026-03-19
**Advisor sentence**: This codebase has critical gaps that, taken together, prevent
research-grade use in its current form — specifically, the data collection pipeline is
non-functional, independent control of scene variables for counterfactual generation is
impossible, and no public API exists for reading or describing scene state in a format an
LLM tool can consume.

---

## 1. Module Map

### Package Root

**`interphyre/__init__.py`** — Entry point. Exports the primary public API: `InterphyreEnv`,
`InterventionContext`, `Level`, `SimulationConfig`, `list_levels`, `__version__`. Version
string is static (`"0.0.1"`) and not auto-synced from `setup.py`.

### Core Modules

**`interphyre/config.py`** — Physics constants and the `SimulationConfig` dataclass. Defines
world bounds (`MAX_X`, `MIN_X`, etc.), solver iteration counts, timing parameters, and
`PerformanceProfiler`. Key exports: `PRECISION`, `SimulationConfig`, `PerformanceProfiler`.
Contains a stale docstring: `velocity_iters` and `position_iters` defaults are 15 and 20 in
code but documented as 6 and 2. The `enable_interventions` flag name implies broader control
than it delivers (only gates snapshot allocation, not trigger evaluation).

**`interphyre/level.py`** — The `Level` dataclass: `name`, `objects`, `action_objects`,
`success_condition`, `metadata`, plus mutators `move_object`, `set_angle`, `change_color`,
`remove_object`, `set_dynamic`, `set_restitution`, `set_friction`, `clone`. The mutators
apply to the data model only — calling `move_object` after `reset()` has no effect on the
running physics world. No `describe()` or `to_text()` method. `metadata` is an untyped
`dict` with no schema.

**`interphyre/environment.py`** — `InterphyreEnv`, the main Gymnasium environment, and
`InterventionContext`. The RL-facing API is `reset()`, `step()`, `render()`, `close()`,
`action_space`, `observation_space`. The intervention API adds `run_until()`, `restore()`,
`step_until()`, `intervention_context()`, `add_object()`, `remove_object()`,
`apply_impulse()`, `apply_force()`, `set_velocity()`, `set_position()`, `freeze()`. The
research API adds `simulate()`, `get_contact_log()`, `get_contact_statistics()`,
`get_level_info()`, `get_performance_stats()`. Contains the most critical structural issues
in the codebase (see Dimension 1–5 findings).

**`interphyre/engine.py`** — `Box2DEngine`: manages the Box2D physics world, body creation,
contact tracking, stationary detection, distance validation. Key exports: `reset()`,
`place_action_objects()`, `get_state()`, `has_contact()`, `world_is_stationary()`,
`is_in_basket()`, `is_in_contact_for_duration()`, `get_contact_log()`,
`get_contact_statistics()`. Contains a correctness bug in `_distance_ball_to_bar()` (uses
initial bar geometry, not live body position), and the contact log is gated behind an
undocumented profiler flag.

### Objects

**`interphyre/objects/base.py`** — `PhyreObject` base class. No `__repr__` or `__eq__`.
Color is an unvalidated string.

**`interphyre/objects/ball.py`** — `Ball(PhyreObject)` and `create_ball()` factory. Ball
angle is stored in the data model but ignored by the physics body (physically correct for
circles, but creates a dead attribute).

**`interphyre/objects/bar.py`** — `Bar(PhyreObject)` with rich constructor classmethods:
`from_endpoints`, `from_point_and_angle`, `from_corner`, `ramp_to_wall`, `touching_wall`,
`support_leg`, `offset_along_angle`. The `ramp_to_wall()` and `touching_wall()` classmethods
divide by `math.sin(angle)` — division by zero for `angle=0` (horizontal bars).

**`interphyre/objects/basket.py`** — `Basket(PhyreObject)` and `create_basket()`. The
`segmented_walls` attribute is stored but `create_basket()` has no corresponding branch —
dead code.

**`interphyre/objects/walls.py`** — `create_walls()`. Walls exist in `engine.bodies` but
not in `level.objects`, creating an asymmetry in state readout.

### Levels

**`interphyre/levels/__init__.py`** — `@register_level` decorator, `load_level()`,
`list_levels()`. All 25 level modules are eagerly imported at `import interphyre` regardless
of which level is needed. `list_levels()` returns alphabetically sorted names only.

**`interphyre/levels/down_to_earth.py`** *(primary research level)* — A single-strategy
level: green ball falls onto purple ground, blocked by an action-placed platform. All five
of the key geometric variables (platform x, platform width, platform y, green ball radius,
action ball radius) are entangled in a single forward RNG sequence. Independent control of
any one variable is not supported via the current API.

**Other levels** — 24 additional levels. All use `cast(dict[str, PhyreObject], objects)` to
silence the type checker, indicating the type system does not verify level construction.
`two_body_problem.py` is the cleanest design and a good RL baseline. `catapult.py` has a
dynamic basket on a tilted ledge that may drift before the action ball arrives.

### Interventions

**`interphyre/interventions/__init__.py`** — Clean public re-export of trigger classes and
`StateSnapshot`. No module-level issues.

**`interphyre/interventions/state.py`** — `StateSnapshot`: `capture()`, `restore()`,
`to_bytes()`, `from_bytes()`. Uses `pickle` for serialization (not version-safe).
`_hash_level()` excludes object shape dimensions (radius, length, thickness) — two
geometrically different scenes with the same object names and positions hash identically.

**`interphyre/interventions/triggers.py`** — Full trigger hierarchy: `TimeBasedTrigger`,
`EventBasedTrigger`, `ConditionBasedTrigger`, `SequenceTrigger`, `AnyTrigger`. Factory
functions: `at_step`, `on_contact`, `on_contact_with`, `on_success`, `when`,
`on_position_threshold`, `on_velocity_threshold`, `on_sequence`, `on_any`. Missing: a
duration-gated contact trigger (ironic given that the success condition uses duration-gated
contact), a world-stationary trigger, and an episode-timeout trigger.

### Render

**`interphyre/render/opencv.py`** — `OpenCVRenderer`. Generates numpy image arrays. Sorts
bodies by y-position for draw order (non-deterministic if two bodies have identical y, in
practice stable due to insertion-order dict iteration). Raises `ValueError` on unsupported
shape types.

**`interphyre/render/pygame.py`** — `PygameRenderer`. Real-time pygame display. Has display
initialization requirements conflicting with headless environments.

**`interphyre/render/video.py`** — `VideoRecorder`. Records simulation to mp4/gif using
OpenCV VideoWriter.

**`interphyre/render/__init__.py`** — Re-exports all renderers plus `save_obs_as_image()`.
The `save_obs_as_image()` utility unnecessarily creates and destroys an `OpenCVRenderer`
instance to convert a discrete image to RGB.

### Agents and Tools

**`agents/random_agent.py`** — `RandomAgent`. `set_seed()` recreates `self.rng`, but all
sampling goes through `action_space.sample()` which uses the gym space's internal RNG.
`self.rng` is never used — `set_seed()` does not control the agent's randomness.

**`agents/evaluation.py`** — `Evaluator`, `EpisodeResult`, `EvaluationMetrics`. Not read in
detail.

**`tools/collect_data.py`** — Data collection pipeline for `(scene, action, outcome)`
datasets. Non-functional as written: `DataCollector._create_env()` at line 370 and
`_verify_action()` at line 483 both call `InterphyreEnv(level=level, config=...)` where
`InterphyreEnv.__init__` takes `level_name: str` as its first positional argument. Passing
`level=level` (a `Level` object) raises `TypeError` immediately.

### Viewer and Demos

**`interphyre/viewer/_viewer.py`** — CLI visualization tool. Hardcodes 600×600 / ppm=60 for
video recording.

**`demos/counterfactuals.py`** — Demonstrates causal branching via snapshot/restore. Calls
`env._step_physics()` (a private method) because no public single-step API exists.

**`demos/quickstart.py`** — Passes a bare `(x, y, radius)` tuple to `step()`, while the
documented format is `List[Tuple[float, float, float]]`. Works due to implicit coercion,
but inconsistent with the docstring.

### Package Configuration

**`setup.py`** — Pins `numpy>=1.26.0,<2.0.0` (excludes numpy 2.x, may conflict with modern
torch). Excludes `agents/` from the installable package, requiring a `sys.path.insert`
workaround in `tools/`.

**`pyproject.toml`** — Ruff configuration only. Suppresses `E402` for `tools/*` to permit
the `sys.path.insert` workaround — a smell that disappears if `agents/` is included in the
package.

---

## 2. Dimension Analysis

### 2.1 API Design & Consistency

**Three parallel paths to object state, none authoritative.** `env.objects` (property,
returns `PhyreObject` data at construction time), `engine.objects()` (method, same data),
`engine.get_state()` (Python tuples, live positions, no velocity), and `env._get_physics_state()`
(private, numpy arrays, live positions + velocity). No single public method returns a
unified, live-state, name-keyed dict of object positions and velocities. The asymmetry
between `get_state()` (tuples) and `_get_physics_state()` (numpy arrays) is undocumented.

**`from_level()` replicates `__init__` body.** `InterphyreEnv.from_level()` at line 267
manually duplicates the entire `__init__` attribute initialization sequence. Any new
attribute introduced in `__init__` must be mirrored in `from_level()`. This maintenance
hazard has already caused the `collect_data.py` bug.

**Action contract ambiguity.** The action space is a flat `Box` of shape `(n_actions × 3,)`.
The step docstring says `List[Tuple[float, float, float]]`. `quickstart.py` passes a bare
tuple. All three work due to implicit coercion inside `step()`, but the user is never told
which form is canonical.

**`run_until()` vs `step_until()` naming.** Both run until a trigger fires. `run_until()`
returns `(StateSnapshot | None, int)`; `step_until()` returns Gym-style
`(obs, reward, terminated, truncated, info)`. The names are indistinguishable from the
call site without reading the signatures.

**`InterventionContext.modify_success_condition()` rollback gap.** `auto_rollback=True` in
`intervention_context()` restores Box2D body state via `StateSnapshot`. It does not restore
Python-level `Level` attributes, including `success_condition`. A context block that
modifies the success condition and then raises will leave the environment permanently
altered.

**Bounds hardcoding.** `_is_within_bounds()` at line 1078 hardcodes `-5.0` / `5.0` rather
than reading `config.MIN_X` / `config.MAX_X`. Changing the world size in config would
silently leave this check broken.

---

### 2.2 LLM Tool-Call Interface

**No scene description method.** The most critical gap for LLM tool-call use: there is no
public function that returns a human-readable or JSON-serializable description of the
current scene. `get_level_info()` returns name and object counts but no positions, sizes,
or colors. `env.objects` returns `PhyreObject` instances with no `__repr__`. The physics
state is accessible only via `_get_physics_state()` (private) or `engine.get_state()`
(tuples, no velocity).

**Contact log gated behind undocumented profiler flag.** `get_contact_log()` and
`get_contact_statistics()` are advertised as research API methods. They return empty results
unless `enable_profiling=True` in `SimulationConfig` (`engine.py:94-103`). This is
documented nowhere in the API docs or demos. An LLM tool calling `get_contact_statistics()`
silently receives zeros.

**No partial simulation API.** The LLM tool-call workflow requires: place action → run N
steps → query state → decide. `run_until(trigger, action=..., max_steps=N)` is the closest
match, but it returns a `StateSnapshot` (not a readable state dict). `simulate()` exists but
does not accept an action and does not call `_place_action_objects()`. The only single-step
interface is `_step_physics()`, which is private and used in `demos/counterfactuals.py` as
an undocumented workaround.

**Return values are not JSON-serializable.** `_get_physics_state()` returns `np.ndarray`.
The contact matrix is a boolean numpy array indexed positionally (not by name). Standard
`json.dumps()` fails on both. An LLM tool framework that serializes return values will crash
or produce unreadable output.

**Functions that should be LLM tools are currently unusable as such:**

| Function | LLM-friendly? | Blocker |
|---|---|---|
| `get_level_info()` | Partial | Missing positions, sizes, colors |
| `get_contact_log()` | No | Empty without profiler; opaque format |
| `run_until(trigger, action)` | No | Returns StateSnapshot, not text |
| `env.objects` | No | PhyreObject has no `__repr__` |
| `engine.get_state()` | Partial | Tuples only, no velocity, no color |
| `simulate(return_trace=True)` | No | Doesn't accept action; numpy arrays |
| `env.success` | Yes | Boolean, clean |

---

### 2.3 Level Architecture

**No enforced level contract.** `Level.__post_init__` checks only that `success_condition`
is callable. It does not verify that `action_objects` names appear in `objects`, that action
objects are `Ball` instances, that required metadata keys are present, or that objects don't
overlap at construction time. Runtime tests (`test_all_levels.py`) catch gross errors, but
structural invariants are not enforced at definition time.

**Freeform metadata.** `level.metadata` is an untyped `dict`. In practice, the only
universal key is `"description"`. The `"action_bounds"` key is consumed by
`_setup_action_space()` — if a level omits it, the fallback uses full world bounds. No
schema, no `TypedDict`, no validation.

**Procedural generation robustness.** In `down_to_earth.py`, all five scene variables
(platform x, platform width, platform y, green ball radius, action ball radius) are drawn
from a single sequential RNG stream. To independently fix one variable while varying
another, the level builder must be bypassed. In `bar.py`, `ramp_to_wall()` and
`touching_wall()` divide by `math.sin(angle)`, which is zero for horizontal bars — a
common case that crashes silently.

**No unsolvable level detection.** A procedurally generated scene may be impossible (e.g.,
a platform spanning both walls). No API-level check warns at construction time.

**Action object placeholder position bug.** The action object is stored in `level.objects`
at `(0, 0)` before placement. The placement validator in `environment.py` may flag valid
actions as colliding if any scene object is near `(0, 0)`.

**Level discoverability.** `list_levels()` returns names only. Querying level metadata
requires instantiating every level. All 25 level modules are eagerly imported at
`import interphyre`, adding startup overhead when only one level is needed.

---

### 2.4 Observation Space

**Contact matrix is positionally indexed, not name-keyed.** The `(i, j)` entry of the
contact boolean matrix corresponds to `object_names[i]` and `object_names[j]`, where
`object_names = list(level.objects.keys())`. A probe model or LLM receiving this matrix
must separately know insertion order. The order is stable within a fixed level but varies
across levels — no unified representation.

**No contact duration or force direction in observation.** The contact matrix records binary
contact state only. Most success conditions use duration-gated contact. The observation does
not expose how long a contact has been active, or the contact normal — both of which are
needed for interpretability probing that targets the "will success occur" computation.

**No trajectory history.** Each step returns a single-frame observation. `simulate(return_trace=True)`
produces a step-indexed trace but is disconnected from the action placement and intervention
workflow (it does not call `_place_action_objects()`). There is no public "run episode from
action, return full trajectory as a list of observations" method.

**Velocity observation bounds are too narrow.** The observation space declares velocity
bounds of `(-10, 10)` m/s. A ball falling from `y=5` under gravity reaches ≈13 m/s before
hitting the ground — exceeding the declared bounds and producing observations that violate
the Gymnasium spec during fast dynamics.

---

### 2.5 Determinism & Reproducibility

**Double initialization corrupts `np_random`.** `InterphyreEnv.__init__` calls `self.reset()`
at line 242 before the caller can supply a seed. `env.np_random` is initialized without a
seed during `__init__`. A subsequent `env.reset(seed=N)` overrides `np_random`, but the
initial `reset()` has already run. The level builder uses its own `rng` (seeded separately
via `load_level(name, seed)`), so in practice this is currently harmless — but any future
level that reads `env.np_random` will produce non-reproducible results.

**`StateSnapshot` uses pickle.** Snapshots written under the current Box2D version may not
restore correctly after a library update. No version tag is stored in the snapshot.

**`_hash_level()` excludes object shape dimensions.** The level hash is computed from
`(name, type, x, y, angle)` per object, ignoring `radius` for balls and `length/thickness`
for bars. Two geometrically different scenes with identical object names and positions will
hash identically. A `StateSnapshot.restore()` that silently succeeds on the wrong scene is
worse than a failed restore.

**`step_index` computed via floating-point division.** `contact_listener.current_time /
config.time_step` is susceptible to off-by-one drift vs. the integer `env.step_count`.

**No cross-platform determinism guarantee.** Box2D uses IEEE 754 arithmetic but does not
pin FPU mode. Reproducibility across x86 and ARM is not documented or tested.

---

### 2.6 Interpretability Research Support

**Dataset generation pipeline is non-functional.** `DataCollector._create_env()` at line
370 and `_verify_action()` at line 483 both call `InterphyreEnv(level=level, config=...)`.
`InterphyreEnv.__init__` takes `level_name: str` as its first positional argument. Passing
`level=level` (a `Level` object) as a keyword raises `TypeError` immediately. The correct
call is `InterphyreEnv.from_level(level, config=...)`. This is the single highest-severity
bug: the primary tool for generating research datasets crashes before producing any data.

**Independent variable control for `down_to_earth` is impossible.** All five scene variables
(platform x, platform width, platform y, green ball radius, action ball radius) are
entangled in a single forward RNG sequence. To fix platform position while varying ball
radius, or vice versa, the level builder function body must be copied and monkey-patched —
there is no parameter-level interface. This blocks counterfactual pair generation, which is
the core dataset requirement for DAS and probing.

**No public trajectory API.** `simulate(return_trace=True)` returns a per-step trace but
does not accept an action argument and does not call `_place_action_objects()`. The demo
workaround calls the private `_place_action_objects()` method first. No public "run episode
from action, return full trajectory" method exists.

**Causal tracing at step T.** `run_until(at_step(T))` correctly captures state at step T.
The returned `StateSnapshot` is opaque — it can be passed to `restore()` but cannot be read
as a data structure. There is no `get_state_at_step(T)` returning a named,
JSON-serializable dict. After `run_until()`, the researcher must manually query each
object's position via `engine.get_state()`, which returns Python tuples (no velocity, no
color, no type).

**`set_position()` does not zero velocity.** An `InterventionContext.set_position()` call
teleports a body but retains its current velocity. This is physically correct for a
"teleport" intervention but may not match the intended semantics for do-calculus
interventions, where setting a body's position should also reset its momentum to avoid
artifact forces from pre-intervention dynamics.

**`_update_relevant_contacts()` uses color-based heuristic.** `engine.py` line 365
identifies relevant contact pairs by checking whether object names contain the substring
`"green"`. This will miss relevant contacts in levels whose success condition depends on
non-green pairs (e.g., `catapult.py`'s blue-green contact). Contact statistics returned for
such levels will be incomplete even with profiling enabled.

---

### 2.7 Documentation & Developer Experience

**Zero documentation for the LLM tool-call workflow.** The primary research use case — an
LLM calling Interphyre via a tool API — has no coverage in `docs/`. There is no page
specifying which functions to expose as tools, the expected input/output schema, how to
convert numpy observations to text, how to use `run_until()` for partial simulation, or how
to generate counterfactual dataset pairs.

**Stale docstrings.** `SimulationConfig` documents `velocity_iters=6` and `position_iters=2`
but code defaults are 15 and 20. The `enable_interventions` flag docstring implies trigger
evaluation is skipped when `False` — actually, only snapshot allocation is skipped; triggers
evaluate on every step regardless.

**Private method in a public demo.** `demos/counterfactuals.py` calls `env._step_physics()`
because there is no public single-step method. This pattern, used in an official demo,
signals that the public API has a gap and normalizes private-method access for users.

**`docs/getting-started.md` running-demo command.** `for f in demos/*.py; do python $f; done`
opens sequential pygame windows without cleanup. Levels with `render_mode="human"` will hang
waiting for the user to close each window.

**`agents/` excluded from the pip package.** `agents/` is excluded from `setup.py`'s
`find_packages()`. Research code depending on `agents.RandomAgent` cannot be installed
cleanly via pip — it works only when executed from the repository root with a
`sys.path.insert` workaround.

---

## 3. Improvement Proposals

### P0: Blocks Research

---

### FIX-COLLECT-DATA

**Category**: Interpretability
**Priority**: P0 — Blocks research
**Effort**: S — hours

**Problem**: `DataCollector._create_env()` at `tools/collect_data.py:370` and
`_verify_action()` at line 483 both call `InterphyreEnv(level=level, config=self.config,
...)`. `InterphyreEnv.__init__` takes `level_name: str` as its first positional argument.
Passing `level=level` (a `Level` object) as a keyword raises `TypeError` immediately,
making the entire data collection pipeline non-functional.

**Proposed fix**: Replace both calls with `InterphyreEnv.from_level(level,
config=self.config, ...)`. Verify with a single-seed smoke test that `collect_data.py
--level down_to_earth --seeds 1` completes without error.

**Research impact**: The `(scene, action, outcome)` dataset is the input to all downstream
interpretability work (probing, DAS, steering). Without a working collection pipeline, no
dataset exists.

---

### ADD-SCENE-DESCRIPTION

**Category**: LLM Interface
**Priority**: P0 — Blocks research
**Effort**: M — 1-2 days

**Problem**: No public method returns a text or JSON-serializable description of the current
scene state. `get_level_info()` omits positions, sizes, and colors. `_get_physics_state()`
is private and returns numpy arrays. `PhyreObject` has no `__repr__`. An LLM tool-calling
Interphyre cannot determine "where is the green ball" via any public API.

**Proposed fix**: Add two methods:
- `Level.describe() -> dict`: Returns a JSON-serializable dict with per-object name, type,
  color, position (x, y), size (radius/length/width as applicable), dynamic flag, and the
  success condition description string.
- `InterphyreEnv.get_state_text() -> dict`: Returns the same information but with live
  physics state (current position, velocity, angle, angular velocity from the engine), plus
  current contact pairs as a `list[tuple[str, str]]` (name-keyed, not positionally indexed),
  plus step count and success flag.

Both return values must be `json.dumps()`-serializable (no numpy arrays, no Box2D objects).

**Research impact**: Every LLM tool-call experiment requires the LLM to observe scene state.
This is the foundational gap in the tool-call interface.

---

### FIX-CONTACT-LOG-GATE

**Category**: LLM Interface / Interpretability
**Priority**: P0 — Blocks research
**Effort**: S — hours

**Problem**: `get_contact_log()` and `get_contact_statistics()` are documented as research
APIs but return empty/zero results by default because `contact_events` is only populated
when `self.profiler is not None` (`engine.py:94-103`). `enable_profiling=False` by default.
This is undocumented. An LLM or probe model using these methods receives silently incorrect
data.

**Proposed fix**: Decouple contact event logging from the performance profiler. Always
populate `contact_events` (or a renamed `contact_log`). The `PerformanceProfiler` should
be a separate opt-in layer on top of basic contact tracking, not the gating condition for
it. Alternatively, default `enable_profiling=True` and document the memory implications.

**Research impact**: Contact duration and contact statistics are the primary signals for
success prediction. Probing experiments that query contact state silently operate on empty
data.

---

### ADD-PARAMETERIZED-LEVEL-BUILDER

**Category**: Interpretability / Level Architecture
**Priority**: P0 — Blocks research
**Effort**: M — 1-2 days

**Problem**: In `down_to_earth.py`, all five scene variables (platform x, platform width,
platform y, green ball radius, action ball radius) are drawn from a single sequential RNG
stream. To independently vary one while holding others fixed, the level builder must be
copied and monkey-patched. No parameter-level control exists. This makes counterfactual
pair generation — a core dataset requirement for DAS and probing — impossible via the
public API.

**Proposed fix**: Refactor `build_level(seed)` to accept an optional `params: dict`
argument:
```python
def build_level(seed: int, params: dict | None = None) -> Level
```
When `params` is provided, override the corresponding `rng.uniform(...)` draws with fixed
values. Document the parameter names (`platform_x`, `platform_width`, `platform_y`,
`green_ball_radius`, `red_ball_radius`) and their valid ranges. Extend the `load_level()`
API to forward `params` to the builder: `load_level("down_to_earth", seed=42, params={...})`.

**Research impact**: The counterfactual dataset structure for DAS and probing requires pairs
of scenes that differ in exactly one variable. Without this, researchers must bypass the API
entirely.

---

### ADD-PUBLIC-STEP-ONE-FRAME

**Category**: LLM Interface / API
**Priority**: P0 — Blocks research
**Effort**: S — hours

**Problem**: The only single-frame stepping method is `_step_physics()`, which is private.
The official demo `demos/counterfactuals.py` calls this private method because no public
equivalent exists. The LLM tool-call workflow requires "place action → step N frames →
query state → step N more frames." This workflow cannot be expressed via public API.

**Proposed fix**: Expose a public `step_physics(n: int = 1) -> dict` method that advances
the simulation by `n` physics frames and returns a readable state dict (same format as
`get_state_text()`). Optionally, add `place_action(action) -> dict` as a separate step
from `step()`, so that action placement and simulation can be interleaved explicitly.

**Research impact**: Multi-step reasoning, causal tracing, and counterfactual branching all
require advancing the simulation in discrete steps with state queries between steps.

---

### P1: Significant Friction

---

### UNIFY-INIT-FROM-LEVEL

**Category**: API
**Priority**: P1 — Significant friction
**Effort**: M — 1-2 days

**Problem**: `InterphyreEnv.from_level()` at line 267 manually replicates the entire
`__init__` attribute initialization sequence. Any new attribute added to `__init__` must
be mirrored in `from_level()`. This has already caused the `collect_data.py` bug.

**Proposed fix**: Refactor so that `__init__` accepts either a `level_name: str` or a
`Level` object, dispatching internally. Alternatively, have `from_level()` delegate to a
shared private `_initialize(level: Level)` method that both constructors call. Either
approach eliminates the duplicated attribute list.

**Research impact**: Prevents the same class of bug from recurring when new environment
attributes are added (e.g., trajectory buffer, tool-call hook).

---

### FIX-SNAPSHOT-HASH

**Category**: Determinism
**Priority**: P1 — Significant friction
**Effort**: S — hours

**Problem**: `StateSnapshot._hash_level()` at `state.py:348` hashes `(name, type, x, y, angle)`
per object but not shape dimensions (`radius` for `Ball`, `length/thickness` for `Bar`,
`bottom_width/height` for `Basket`). Two geometrically different scenes with identical
object names and positions hash identically. A `restore()` that silently succeeds on the
wrong scene corrupts trajectory replays.

**Proposed fix**: Include shape-defining dimensions in the hash tuple. For `Ball`, add
`obj.radius`. For `Bar`, add `obj.length` and `obj.thickness`. For `Basket`, add
`obj.bottom_width`, `obj.top_width`, and `obj.height`.

**Research impact**: Silent snapshot restoration on the wrong scene geometry corrupts
counterfactual datasets and causal tracing experiments without any error signal.

---

### REPLACE-PICKLE-SERIALIZATION

**Category**: Determinism
**Priority**: P1 — Significant friction
**Effort**: M — 1-2 days

**Problem**: `StateSnapshot` uses `pickle` for serialization (`state.py:165, 192`). Pickle
is not version-safe across Box2D updates. A snapshot created under Box2D 2.3.x may not
restore correctly after a library update, silently replaying incorrect physics. No version
tag is stored in snapshots.

**Proposed fix**: Replace pickle with a structured serialization format (JSON or msgpack)
that captures physics state as explicit fields: body position, angle, linear velocity,
angular velocity for each named body. Store a version tag (Box2D version + Interphyre
version) in the snapshot header.

**Research impact**: Reproducible datasets stored as snapshots may become unrestorable after
dependency updates, losing experimental continuity across software versions.

---

### FIX-CONTACT-MATRIX-NAME-KEYED

**Category**: Observation
**Priority**: P1 — Significant friction
**Effort**: S — hours

**Problem**: The contact matrix in the observation is a boolean `(N, N)` numpy array indexed
by position into `list(level.objects.keys())`. An LLM or probe model receiving this matrix
must separately know the insertion-order-dependent key ordering to interpret which `(i, j)`
entry refers to which pair of objects.

**Proposed fix**: Change the contact representation to a `list[tuple[str, str]]` of
currently-in-contact object name pairs. For backward compatibility with RL code that expects
the matrix format, keep the matrix under `"contact_matrix"` and add a `"contact_pairs"` key
with the name-keyed list.

**Research impact**: Probe models for contact prediction and LLM tools that query contact
state both require human-readable contact representation.

---

### FIX-VELOCITY-OBSERVATION-BOUNDS

**Category**: Observation
**Priority**: P1 — Significant friction
**Effort**: S — hours

**Problem**: The observation space declares velocity bounds of `(-10, 10)` m/s. A ball
falling from `y=5` under gravity reaches ≈13 m/s by ground impact. Fast collisions produce
even higher peak velocities. Observations routinely violate the declared bounds during
normal play.

**Proposed fix**: Increase velocity bounds to `(-50, 50)` m/s (conservative upper bound for
typical Box2D scenes at the default gravity setting) or make the bound configurable via
`SimulationConfig`. Document the chosen bound and the physics basis for it.

**Research impact**: Gymnasium-compliant RL training frameworks check observation space
bounds. Out-of-bounds observations may trigger assertions or produce log warnings that
pollute training runs.

---

### ADD-CONTACT-DURATION-TRIGGER

**Category**: API / Interpretability
**Priority**: P1 — Significant friction
**Effort**: S — hours

**Problem**: The trigger system has no duration-gated contact trigger. The success condition
for most levels is `is_in_contact_for_duration(obj_a, obj_b, duration)` — but no equivalent
trigger exists to stop the simulation when sustained contact begins. `run_until()` cannot
express "stop when the success contact duration is reached."

**Proposed fix**: Add `on_contact_duration(obj_a: str, obj_b: str, min_seconds: float)`
trigger factory. Fire when `is_in_contact_for_duration(obj_a, obj_b, min_seconds)` returns
True.

**Research impact**: Causal tracing experiments that wish to capture state "at the moment
success becomes assured" cannot express this condition via the trigger API.

---

### FIX-ROLLBACK-SUCCESS-CONDITION

**Category**: API
**Priority**: P1 — Significant friction
**Effort**: S — hours

**Problem**: `InterventionContext.modify_success_condition()` mutates `level.success_condition`
directly and is not registered with the `StateSnapshot`-based auto-rollback. A
`with intervention_context(auto_rollback=True)` block that modifies the success condition
and then raises will leave the environment with the altered condition permanently.

**Proposed fix**: Before mutating `success_condition`, store the original in the
`InterventionContext` instance. Restore it in `__exit__` when `auto_rollback=True`,
regardless of whether an exception occurred.

**Research impact**: Counterfactual analysis that tests alternative success criteria inside
a context block currently pollutes the environment state on exception.

---

### ADD-TRAJECTORY-API

**Category**: Interpretability
**Priority**: P1 — Significant friction
**Effort**: S — hours

**Problem**: `simulate(return_trace=True)` returns a per-step trace but does not accept an
action argument and does not call `_place_action_objects()`. To get a full trajectory from
an action, a user must call the private `_place_action_objects()` first.

**Proposed fix**: Add a public `run_episode(action, max_steps: int = 240, return_trace: bool = False)`
method that (1) calls `_place_action_objects(action)`, (2) steps physics for up to
`max_steps` frames (stopping on `terminated`), and (3) returns either the terminal
observation or a list of per-step state dicts (from `get_state_text()`).

**Research impact**: DAS and probing experiments need step-indexed trajectory histories.
Without a public trajectory method, every researcher independently implements the
private-method workaround.

---

### FIX-ENGINE-BAR-CONTACT-DISTANCE

**Category**: API
**Priority**: P1 — Significant friction
**Effort**: S — hours

**Problem**: `Box2DEngine._distance_ball_to_bar()` at `engine.py:638` reads `bar_obj.angle`,
`bar_obj.x`, `bar_obj.y` from the original `Bar` data object (construction-time values).
For dynamic bars that rotate during simulation, the contact validation distance is computed
against the bar's initial geometry, not its current physics state. Contact validation is
incorrect for any dynamic rotating bar.

**Proposed fix**: Replace the `bar_obj` parameter with the corresponding Box2D body from
`engine.bodies`. Read `body.position` and `body.angle` for the current state. Retrieve the
bar's half-length from the Box2D fixture shape rather than the data object.

**Research impact**: `catapult.py` and any level with a dynamic rotating bar will return
incorrect contact validation results, leading to silently wrong success evaluation.

---

### FIX-RELEVANT-CONTACTS-COLOR-HEURISTIC

**Category**: API
**Priority**: P1 — Significant friction
**Effort**: S — hours

**Problem**: `engine._update_relevant_contacts()` at line 365 identifies relevant contact
pairs by checking whether object names contain the substring `"green"`. This misses contacts
in levels whose success condition involves non-green object pairs. Contact statistics for
such levels are incomplete even with profiling enabled.

**Proposed fix**: Remove the color-string heuristic. Derive the relevant contact pairs from
`Level.success_condition` at construction time, or track all contact pairs and let the
success condition evaluate on the full contact graph.

**Research impact**: `get_contact_statistics()` silently returns wrong data for non-green
success conditions, corrupting contact-based features in probe models.

---

### ADD-LLM-TOOL-DOCS

**Category**: Docs
**Priority**: P1 — Significant friction
**Effort**: M — 1-2 days

**Problem**: The primary research use case — an LLM calling Interphyre as a tool API — has
zero coverage in `docs/`. There is no page specifying which functions to expose as tools,
what the expected input/output schema is, how to convert observations to text, or how to
generate counterfactual datasets.

**Proposed fix**: Add `docs/llm-tool-call.md` covering: (1) recommended tool set (functions
to expose), (2) input/output schemas for each, (3) a worked example of a multi-step LLM
interaction, (4) how to use `run_until()` for partial simulation, and (5) the
counterfactual dataset generation pattern.

**Research impact**: Every new collaborator must reverse-engineer the tool-call workflow
from the codebase. A documentation page saves days of onboarding per person.

---

### P2: Quality and Completeness

---

### FIX-CONFIG-DOCSTRING

**Category**: Docs
**Priority**: P2 — Nice to have
**Effort**: S — hours

**Problem**: `SimulationConfig` docstring states `velocity_iters=6` and `position_iters=2`.
Actual code defaults are 15 and 20 (`config.py`). The `enable_interventions` docstring
implies trigger evaluation is skipped when `False` — actually, only snapshot allocation is
skipped.

**Proposed fix**: Update both docstrings to match the code. Add a note to
`enable_interventions` clarifying that triggers always evaluate; the flag controls snapshot
pre-allocation only.

**Research impact**: Users who tune solver parameters based on the docstring will use
incorrect defaults in their configs.

---

### REMOVE-DEAD-CODE

**Category**: API
**Priority**: P2 — Nice to have
**Effort**: S — hours

**Problem**: Three items: (1) `segmented_walls: bool = False` in `Basket.__init__` with no
corresponding branch in `create_basket()`. (2) `_active_interventions` is populated from
`options["interventions"]` at reset (`environment.py:862`) but never consumed during the
simulation rollout. (3) `RandomAgent.rng` is created and seeded but all sampling goes
through `action_space.sample()`, making `set_seed()` ineffective.

**Proposed fix**: (1) Remove `segmented_walls` from `Basket` and `create_basket()`. (2)
Remove the `_active_interventions` accumulation or connect it to the trigger evaluation
loop. (3) Fix `RandomAgent.set_seed()` to also call `self.action_space.seed(seed)`, or
remove `self.rng` and document that seeding goes through `set_seed()` → `action_space.seed()`.

**Research impact**: The `RandomAgent` seeding bug means reproducibility claims for
random-agent baselines are incorrect — `set_seed()` has no effect on the sampling
distribution.

---

### FIX-BOUNDS-HARDCODING

**Category**: API
**Priority**: P2 — Nice to have
**Effort**: S — hours

**Problem**: `environment._is_within_bounds()` at line 1078 hardcodes `-5.0` and `5.0`
rather than reading `config.MIN_X / MAX_X`. If world bounds are modified in
`SimulationConfig`, this check silently becomes inconsistent.

**Proposed fix**: Replace hardcoded values with `self._config.MIN_X`, `self._config.MAX_X`,
`self._config.MIN_Y`, `self._config.MAX_Y`.

---

### FIX-BAR-DIVISION-BY-ZERO

**Category**: Level Architecture
**Priority**: P2 — Nice to have
**Effort**: S — hours

**Problem**: `Bar.ramp_to_wall()` and `Bar.touching_wall()` divide by `math.sin(angle)` to
compute bar length from wall distance. For `angle=0` (horizontal bar), `math.sin(0) = 0`
causes `ZeroDivisionError` — a common degenerate case.

**Proposed fix**: Add a guard: if `abs(math.sin(angle)) < 1e-6`, raise
`ValueError("ramp_to_wall() requires non-horizontal angle")` with a clear message.
Document the angle constraint in the method docstring.

---

### FIX-STATIONARY-DETECTION-DEQUE

**Category**: API
**Priority**: P2 — Nice to have
**Effort**: S — hours

**Problem**: `Box2DEngine.world_is_stationary()` maintains a velocity history list and calls
`list.pop(0)` at `engine.py:556`. `pop(0)` is O(N) due to list shifting. At 60 fps with a
history window of W steps, this is 60W list operations per second.

**Proposed fix**: Replace `list` with `collections.deque(maxlen=W)`. Deque `popleft()` is
O(1).

---

### ADD-LEVEL-METADATA-SCHEMA

**Category**: Level Architecture
**Priority**: P2 — Nice to have
**Effort**: M — 1-2 days

**Problem**: `level.metadata` is an untyped `dict`. The `"action_bounds"` key is consumed
by `_setup_action_space()` but not validated at definition time. No schema, no required vs.
optional key distinction, no ability to filter levels by metadata without instantiation.

**Proposed fix**: Define `LevelMetadata(TypedDict)` with at minimum:
```python
class LevelMetadata(TypedDict, total=False):
    description: str           # required
    action_bounds: dict        # optional
    difficulty: str            # optional
    n_action_objects: int      # optional
```
Validate `metadata["description"]` in `Level.__post_init__`. Update `list_levels()` to
optionally return metadata alongside names, enabling level filtering without instantiation.

---

### ADD-AGENTS-TO-PACKAGE

**Category**: Developer Experience
**Priority**: P2 — Nice to have
**Effort**: S — hours

**Problem**: `agents/` is excluded from `setup.py`'s `find_packages()`. Code depending on
`agents.RandomAgent` requires a `sys.path.insert` workaround and only works from the
repository root.

**Proposed fix**: Remove `"agents"` from the `exclude` list in `find_packages()`. Remove
the `E402` exception for `tools/*` in `pyproject.toml` once the `sys.path.insert`
workarounds are eliminated.

---

## 4. Cross-Cutting Observations

### The RL Interface and the Research Interface Are Architecturally Merged but Semantically Divergent

`InterphyreEnv` was designed as a Gymnasium environment and later extended with research
capabilities (interventions, contact logging, trajectory traces). The result is a class that
satisfies both use cases on the surface but serves neither optimally. The RL interface
demands a fixed observation space, a single `step()` that runs to episode completion, and a
simple `reset(seed)` for reproducibility. The research interface demands partial simulation,
named-object state queries, JSON-serializable returns, and independent variable control. The
same class tries to serve both, and the seams show: `step()` runs a full episode (RL
semantics), but the intervention API wraps it in a context manager that can branch
mid-episode (research semantics). The `simulate()` method was added for research use but
doesn't place action objects and isn't integrated with the intervention workflow. This
architectural merger is the source of approximately half the P0 and P1 issues in this audit.

### Two RNG Streams With No Unified Seeding Contract

Interphyre manages two separate random streams with no documented contract for their
interaction: the level builder's `rng` (seeded via `load_level(name, seed)`) and
`env.np_random` (seeded via `reset(seed=...)`). The level builder does not read from
`env.np_random`, and `env.np_random` is not used for level geometry — so in practice the
two streams are currently independent. But the API surface implies a unified seed: users
expect `InterphyreEnv("down_to_earth", seed=42)` followed by `reset(seed=42)` to fully
determine the scene. The double `reset()` in `__init__` (once unseeded, once with the user
seed) introduces a latent inconsistency that will manifest as a subtle reproduction failure
the first time any level builder or intervention draws from `env.np_random`. This needs a
clear, documented contract — ideally: one seed argument, one RNG stream, fully deterministic
from call site to physics body.

### The Tool-Call Use Case Is Unsupported at the Infrastructure Level

Every component of the LLM tool-call workflow — scene description, contact querying,
partial simulation, JSON-serializable state — requires either a private method, a
post-processing wrapper, or functionality that doesn't exist yet. The contact log is gated
behind a profiler flag. State is returned as numpy arrays. The single-step API is private.
Level variables are not independently controllable. Each of these is a separate bug, but
together they represent a structural gap: the tool-call interface is an afterthought, not a
design target. The P0 proposals in this report address the immediate blockers, but a more
durable fix would be to design a thin `InterphyreTool` wrapper class that presents only the
JSON-serializable, LLM-friendly API surface, delegating to the existing `InterphyreEnv`
internals. This would keep the Gymnasium interface stable while evolving the tool-call
interface independently.

### Procedural Level Generation and Interpretability Research Are Structurally Incompatible

The level builder design pattern — a single `build_level(seed) -> Level` function that
draws all geometric variables from a forward RNG sequence — is correct for RL training,
where scene diversity is the goal and individual variables need not be controlled. For
interpretability research, this design is fundamentally wrong: the central requirement is
*independent* variation of one variable while holding all others fixed. The
`down_to_earth.py` level entangles five scene variables in a single RNG sequence with no
public override mechanism. This is not an oversight; it is the natural consequence of
designing the level API exclusively for the RL use case. The parameterized builder proposal
(P0 above) is a surgical fix, but the deeper recommendation for v0.0.2 is to define a
second-class level API: `build_level_from_params(params: LevelParams) -> Level` alongside
`build_level(seed)`. The parameterized form serves research; the seed form serves RL. Both
should be first-class citizens.

### StateSnapshot Is the Reproducibility Backbone but Has Three Independent Failure Modes

`StateSnapshot` is the mechanism that makes causal tracing, counterfactual branching, and
trajectory replay possible. It is doing important work. But it currently has three
independent failure modes: (1) pickle-based serialization is not version-safe across library
updates; (2) the level hash excludes shape dimensions, so a restore can silently succeed on
the wrong scene geometry; (3) the rollback mechanism restores Box2D body state but not
Python-level `Level` attributes (including the success condition). Any one of these can
produce a silent incorrect result — a trajectory that appears to replay correctly but uses
wrong geometry, or a success condition that was permanently altered before the snapshot was
captured. Because interpretability experiments rely on precise counterfactual replay, even a
small fraction of silently incorrect snapshots undermines the entire dataset. These three
bugs should be treated as a single compound fix: structured serialization, full hash
(including shape dimensions), and rollback coverage for all mutable Level attributes.
