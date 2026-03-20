# Interphyre Codebase Module Map

Produced by: interphyre-76n.1 (codebase_audit / scan)
Date: 2026-03-19

---

## Package Root

### `interphyre/__init__.py`
**Purpose**: Package entry point. Exports the primary public API.
**Public API**: `InterphyreEnv`, `InterventionContext`, `Level`, `SimulationConfig`, `list_levels`, `__version__`
**Internal deps**: environment, level, config, levels
**Issues**: Version string is `"0.0.1"` (static, not synced from setup.py automatically).

---

## Core Modules

### `interphyre/config.py`
**Purpose**: Physics simulation constants, the `SimulationConfig` dataclass, and `PerformanceProfiler`.
**Public API**: `PRECISION`, `CONTACT_DISTANCE_TOLERANCE`, `MAX_X/MIN_X/MAX_Y/MIN_Y/WORLD_WIDTH/WORLD_HEIGHT`, `SimulationConfig`, `PerformanceProfiler`
**Internal deps**: none
**Issues**:
- Docstring for `SimulationConfig` says `velocity_iters` default is 6 and `position_iters` default is 2. Actual code defaults are 15 and 20 respectively — docstring is stale.
- `validate_contact_distance` defaults to `False` (disabled) while `track_all_contacts` defaults to `True`. These interact confusingly: contact events are tracked but never validated unless explicitly enabled.
- `default_success_time = 3.0` is quite long (at 60 fps this means 180 consecutive steps of contact) — this is a hidden parameter that controls how hard levels are; it is not documented in level metadata.
- `PerformanceProfiler` uses `time.perf_counter()` which is wall-clock, not deterministic across runs.

---

### `interphyre/level.py`
**Purpose**: The `Level` dataclass — the central data structure for a puzzle scene.
**Public API**: `Level` (name, objects, action_objects, success_condition, metadata), plus mutator methods: `move_object`, `set_angle`, `change_color`, `remove_object`, `set_dynamic`, `set_restitution`, `set_friction`, `clone`
**Internal deps**: `interphyre.objects.PhyreObject`
**Issues**:
- `__post_init__` validates only that `success_condition` is callable. No validation that `action_objects` names exist in `objects`.
- `metadata` field has no schema; every level uses a freeform dict. The only consistent key in practice is `"description"`. There is no `"action_bounds"`, `"difficulty"`, or other research-relevant metadata in most levels, except for `"action_bounds"` which is read by `_setup_action_space()` in the environment.
- `clone()` deep-copies objects and metadata but shallow-copies `success_condition` (a closure). If the success condition captures mutable state, the clone shares it. In practice closures are pure functions so this is safe, but it is an undocumented assumption.
- No `describe()` or `to_text()` method for producing a natural-language scene description — a critical gap for LLM tool-call usage.
- Level mutations (`move_object`, etc.) apply only to the data model, not to the physics world. Calling `move_object` after `reset()` has no effect on the running simulation without rebuilding the world.

---

### `interphyre/environment.py`
**Purpose**: `InterphyreEnv` — the main Gymnasium environment class. Also contains `InterventionContext`.
**Public API (RL)**: `reset()`, `step()`, `render()`, `close()`, `action_space`, `observation_space`, `level`, `objects`, `success`
**Public API (Intervention)**: `run_until()`, `restore()`, `step_until()`, `intervention_context()`, `add_object()`, `remove_object()`, `apply_impulse()`, `apply_force()`, `set_velocity()`, `set_position()`, `freeze()`
**Public API (Research)**: `simulate()`, `get_contact_log()`, `get_contact_statistics()`, `get_level_info()`, `get_performance_stats()`
**Internal deps**: engine, level, config, render, objects, interventions
**Issues**:
- `__init__` calls `self.reset()` unconditionally at line 242. This means the environment is partially initialized before the caller can see it, and the initial `reset()` uses the seed passed at construction time — but `reset(seed=...)` called later will use a *different* seed for numpy's internal state. This is a subtle seeding inconsistency: `self.np_random` is set from `np.random.default_rng()` (no seed) during `__init__`, only overridden if `reset(seed=...)` is called later.
- `from_level()` factory at line 267 manually replicates the entire `__init__` body. This dual-path initialization creates a maintenance hazard — any new `__init__` attribute will need to be added to both places.
- The human renderer in `__init__` (line 213) ignores the `image_size` and `image_ppm` parameters and hardcodes `PygameRenderer(width=600, height=600, ppm=60)`, making those kwargs irrelevant for `render_mode="human"`.
- `_is_within_bounds()` (line 1078) hardcodes `-5.0` and `5.0` world bounds instead of using `config.MAX_X/MIN_X`. If config bounds are ever changed, this will silently break.
- `_get_image_observation()` (line 1233) creates a new `OpenCVRenderer` object on every observation call — O(1) allocations per step, minor but avoidable.
- `step()` returns `terminated=True` for invalid actions with `reward=-1.0` (line 916). This gives a reward signal for invalid actions but is semantically odd since nothing happened. The policy can learn to exploit this.
- There is no `place_action()` method separate from `step()`. The only way to place the action ball without triggering the full simulation is to use `run_until(at_step(0))`, which is not documented and feels like a hack.
- `simulate()` (line 1291) exists as a public debugging method but is not in the Gym API and does not call `_place_action_objects()`. It shares the physics stepping loop with `_run_simulation_rollout()` but has no unified implementation — two nearly identical loops.
- `InterventionContext.modify_success_condition()` (line 113) mutates `self._env._level.success_condition` directly with no undo path (even if `auto_rollback=True`). The auto-rollback (`StateSnapshot`) only restores Box2D body state, not Python-level level attributes.
- `_active_interventions` is allocated and populated from `options["interventions"]` at reset (line 862) but is never actually consumed during the simulation rollout — it accumulates without being applied. Dead code pattern.
- No way to query the current state as a text description. `get_level_info()` returns object counts and types, not positions or physics state in a text-serializable format.

---

### `interphyre/engine.py`
**Purpose**: `Box2DEngine` manages the Box2D physics world — body creation, contact tracking, stationary detection, distance validation.
**Public API**: `reset()`, `place_action_objects()`, `get_state()`, `objects()`, `has_contact()`, `world_is_stationary()`, `is_in_basket()`, `is_in_contact_for_duration()`, `get_contact_duration()`, `get_contact_log()`, `get_contact_statistics()`
**Internal deps**: config, level, objects
**Issues**:
- **Bug**: `_distance_ball_to_bar()` at line 638 takes `bar_obj` (the original `Bar` data object) rather than the Box2D body. It reads `bar_obj.angle`, `bar_obj.x`, `bar_obj.y` — the initial construction-time values. During simulation, if a bar is dynamic and rotates, the contact validation distance is computed against the bar's *initial* position/angle, not its current physics state. This is a correctness bug in contact validation for dynamic bars. (Static bars are unaffected since they don't move.)
- `GoalContactListener.contact_events` (the list backing `get_contact_log()`) is only populated when `self.profiler` is not `None` (line 94-103). Since `enable_profiling=False` by default, `contact_events` is always empty and `get_contact_log()` / `get_contact_statistics()` return empty/zero data by default. These are advertised as "research" methods but require enabling profiling first — this is not documented.
- `get_state()` (line 450) returns positions as Python tuples, while `_get_physics_state()` in `environment.py` (line 1187) returns numpy arrays. Two public state-reading methods with inconsistent types.
- `objects()` (line 506) is defined as a method (not a property) returning `level.objects`. But `Box2DEngine.objects` collides semantically with the `bodies` attribute — confusing naming. There is also `env.objects` (a property on `InterphyreEnv`), making three ways to access scene objects.
- `_update_relevant_contacts()` (line 365) adds all contacts involving "green" objects and action objects to the relevant_pairs set. This heuristic is color-based string matching (`"green" in obj_name.lower()`), which will miss relevant contacts in levels whose success condition depends on non-green object pairs (e.g., the `catapult` level's blue-green contact).
- `world_is_stationary()` uses a velocity history list with pop(0) (line 556) — O(N) per step due to list shifting. Should use a deque.
- Contact invalidation is tracked via `invalidate_contact()` which adds an entry to `contact_events` only if `self.profiler` is set — same logging gate issue.
- `is_in_basket()` (line 583) iterates all world contacts O(n) to find sensor overlaps, instead of using the contact_listener set. Inconsistency in how contact state is queried.

---

## Objects

### `interphyre/objects/base.py`
**Purpose**: `PhyreObject` base class defining shared physics properties.
**Public API**: `PhyreObject(x, y, angle, color, dynamic, restitution, friction, linear_damping, angular_damping, density)`
**Issues**:
- No `__repr__` or `__eq__`, making debugging and serialization harder.
- `color` is a string with no validation — any string is accepted but only 8 colors render correctly.
- `angle` is in degrees here but converted to radians in `create_bar` and `create_basket` — this conversion happens in the factory functions, not centrally.

### `interphyre/objects/ball.py`
**Purpose**: `Ball(PhyreObject)` — circular objects. `create_ball()` factory.
**Public API**: `Ball(x, y, radius, **kwargs)`, `create_ball(world, ball, name, use_ccd)`
**Issues**:
- `create_ball()` always sets `angle=0` for both dynamic and static bodies (line 74-87). A ball's `angle` attribute in `PhyreObject` is effectively ignored by the physics body. This is physically reasonable for circles but means a Ball's `.angle` attribute is a dead property.

### `interphyre/objects/bar.py`
**Purpose**: `Bar(PhyreObject)` — rectangular objects with rich constructor patterns. `create_bar()` factory.
**Public API**: `Bar(x, y, length, angle, thickness, ...)`, classmethods: `from_endpoints`, `from_point_and_angle`, `from_corner`, `ramp_to_wall`, `touching_wall`, `support_leg`, `offset_along_angle`. `create_bar()`.
**Issues**:
- `ramp_to_wall()` and `touching_wall()` compute distances via trigonometric division. For `wall_side="top"` or `"bottom"` when `angle=0`, `math.sin(0) = 0` → division by zero. These methods will crash silently on degenerate inputs.
- `Bar._update_endpoints()` and `_update_center_from_endpoints()` are private helpers that keep two coordinate representations (center+angle vs endpoints) in sync. Property setters re-invoke these. This is correct but complex; if a level directly assigns `bar._x = value` bypassing the setter, the endpoints become stale. No real protection against this.

### `interphyre/objects/basket.py`
**Purpose**: `Basket(PhyreObject)` — U-shaped container. `create_basket()` factory.
**Public API**: `Basket(x, y, bottom_width, top_width, height, scale, ...)`, `calculate_dimensions()`, `get_anchor_offset()`. `create_basket()`.
**Issues**:
- `segmented_walls: bool = False` is stored in `__init__` but `create_basket()` has no branch for segmented walls. It is dead code.
- `_circle_intersects_basket()` in `environment.py` (line 1122) uses `basket.total_width` / `basket.total_height` for AABB collision and does not account for the basket's anchor offset. A basket with `anchor="center"` is positioned differently than the method assumes, potentially producing incorrect placement validation.
- `create_basket()` is very long (~190 lines) due to the multi-fixture construction.

### `interphyre/objects/walls.py`
**Purpose**: `create_walls()` — creates 4 static boundary bodies.
**Issues**:
- Walls are in `engine.bodies` (with keys `left_wall`, `right_wall`, etc.) but not in `level.objects`. This asymmetry means `get_state()` and `_get_physics_state()` don't include walls, but the walls do generate contacts with game objects. The contact listener will report `(object_name, None)` or similar if the wall body's `userData` leaks into a contact pair — though in practice the wall userData is set and the contact_listener filters on `if a and b`.

---

## Levels

### `interphyre/levels/__init__.py`
**Purpose**: Registry, `@register_level` decorator, `load_level()`, `list_levels()`.
**Public API**: `register_level`, `load_level(name, seed)`, `list_levels()`
**Issues**:
- `load_level()` imports the module on demand, but all modules are also eagerly imported at the bottom of `__init__.py` via `importlib.import_module()`. This means all 25 level modules are always loaded at `import interphyre`, adding startup cost.
- No API to list levels with their metadata (description, difficulty, action object types) without fully instantiating them.
- `list_levels()` returns names sorted alphabetically. There is no type-based or difficulty-based filtering.

### `interphyre/levels/down_to_earth.py` *(primary research level)*
**Purpose**: Single-strategy level — green ball falls onto purple ground, blocked by a platform.
**API**: `build_level(seed) -> Level`
**Issues**:
- `platform_width = rng.uniform(1, 7)` and `platform_x = rng.uniform(-5, 5 - platform_width)`. When `platform_width` is large and `platform_x` is near the lower bound, platform may be very close to the left wall. The green ball is always placed at `platform_x + platform_width/2`, i.e., centered above the platform. This means the green ball's x-position is fully determined by platform geometry — no independent variation in ball placement.
- `green_ball_y = 4.5 - green_ball_radius` (fixed near top). Platform y varies uniformly in [-2, 2]. The vertical distance between ball and platform thus varies, producing levels of varying difficulty that are not parameterized in metadata.
- `red_ball_radius = rng.uniform(0.3, 0.6)` — the action ball radius varies per seed. This affects action difficulty but is not separably controllable from the level layout seed. To vary platform position while holding everything else fixed, the level builder function must be bypassed.
- No guard against the green ball starting inside the platform if `platform_y` is near the top and the ball is placed just above. Platform at y=2 has top at y=2.1; ball at y=4.5-0.5=4.0 — so at least 1.9 units clearance at minimum, no overlap possible.

### `interphyre/levels/catapult.py`
**Purpose**: Launch green ball into basket using a catapult arm and action ball.
**Issues**:
- `basket = Basket(..., dynamic=True)` is placed at the top of a tilted ledge (`angle=ledge_angle`). A dynamic basket on a tilted surface will slide/fall immediately under gravity unless the ledge friction is high enough. This may cause basket position to be poorly reproducible across very slightly different platform angles.
- `pivot_ball` and `catapult_bar` positions are computed as hard arithmetic offsets from platform geometry — no bounds checking.

### `interphyre/levels/two_body_problem.py`
**Purpose**: Simplest level — push green ball into blue ball.
**Issues**: Clean design, no significant issues. Good baseline for LLM experiments.

### `interphyre/levels/basket_case.py`
**Purpose**: Green ball must hit purple ground, potentially trapped by a basket.
**Issues**: Success condition (green_ball on purple_ground) is actually the *opposite* of catching the ball. Metadata says "not trapped in the basket" but success requires hitting the ground — semantically consistent but counterintuitive relative to the level name.

### General Level Issues (across all levels)
- All levels use `cast(dict[str, PhyreObject], objects)` to silence type checker — the cast is correct but indicates the type system doesn't fully verify level construction.
- No validation step catches overlapping static objects before simulation starts.
- The action object placeholder position (0, 0) is stored in `level.objects` but is not physically placed. If the scene has an object near (0, 0), the placement validator in `environment.py` may incorrectly flag valid actions as colliding.
- No "unsolvable level" detection — if procedural generation creates a scene that makes success impossible (e.g., platform extends over the full ground), there is no early warning.

---

## Interventions

### `interphyre/interventions/__init__.py`
**Purpose**: Public API for the intervention system — re-exports triggers and StateSnapshot.
**Public API**: `StateSnapshot`, `Trigger`, `TimeBasedTrigger`, `EventBasedTrigger`, `ConditionBasedTrigger`, `SequenceTrigger`, `AnyTrigger`, `at_step`, `on_contact`, `on_contact_with`, `on_success`, `when`, `on_position_threshold`, `on_velocity_threshold`, `on_sequence`, `on_any`
**Issues**: None at the module level. The module is clean and well-organized.

### `interphyre/interventions/state.py`
**Purpose**: `StateSnapshot` — immutable capture of complete simulation state for replay.
**Public API**: `StateSnapshot.capture(engine, metadata)`, `StateSnapshot.restore(engine)`, `StateSnapshot.to_bytes()`, `StateSnapshot.from_bytes()`
**Issues**:
- Serialization uses `pickle` (lines 165, 192, 392, 405). Pickle is not version-safe across Box2D updates and has security implications if snapshots are loaded from untrusted sources.
- `_hash_level()` (line 348) hashes `(name, type, x, y, angle)` for each object but not shape dimensions (radius for Ball, length/thickness for Bar, bottom_width/height for Basket). Two levels with the same name and positions but different ball radii would produce the same hash — potentially allowing restore to succeed silently on a different scene.
- Contact start times are serialized with `f"{sorted(pair)[0]}|{sorted(pair)[1]}"` (line 280). If object names contain the `"|"` character, this will produce ambiguous keys.
- `step_index` (line 288) is computed from `contact_listener.current_time / config.time_step`. Floating-point division may produce off-by-one indices. The `env.step_count` is updated separately and may drift from this calculation.

### `interphyre/interventions/triggers.py`
**Purpose**: Trigger hierarchy for `run_until()` / `step_until()`.
**Public API**: All trigger classes and factory functions listed above.
**Issues**:
- `enable_interventions` flag in `SimulationConfig` exists and the docstring describes it as "opt-in for zero overhead." But triggers evaluate their conditions on every step regardless of this flag — the flag controls only snapshot allocation overhead, not trigger evaluation. The flag name implies broader control.
- No trigger for sustained contact duration (e.g., "object A in contact with B for > 0.5s"). This is surprising given that the *success condition* in most levels uses duration-gated contact, but the trigger system has no duration trigger.
- No trigger for "episode timeout" or "world stationary" — common conditions for simulation termination in research workflows.
- `SequenceTrigger._current_index` is a mutable field on a `@dataclass` — not frozen, which means copies of a SequenceTrigger will share mutable state if shallow-copied.

---

## Render

### `interphyre/render/base.py`
**Purpose**: `COLORS` dict, `DISCRETE_COLORS` dict (0-7 color indices), `RGB_TO_DISCRETE` reverse map, and abstract `Renderer` base class.
**Issues**:
- `COLORS` includes `"yellow"` and `"white"`, but `DISCRETE_COLORS` does not include yellow (only 7 colors + background). A yellow object cannot be rendered in discrete mode.
- `DISCRETE_COLORS` maps index 7 to `(255, 0, 0)` labeled as "walls (bright red)" but walls are not rendered (filtered in `OpenCVRenderer._get_object_color()`). Index 7 is reserved but unused in practice.

### `interphyre/render/opencv.py`
**Purpose**: `OpenCVRenderer` — generates numpy image arrays without display.
**Public API**: `render(engine)`, `render_discrete(engine)`, `discrete_to_rgb(discrete_image)`
**Issues**:
- `render()` sorts bodies by y-position (line 87) for bottom-to-top draw order. This is a visual ordering choice but is non-deterministic if two bodies have identical y — Python's sort is stable, but body iteration order from `engine.bodies.items()` depends on insertion order, which is reliable in Python 3.7+ but not documented as a spec.
- `render()` raises `ValueError` for unsupported shape types (line 116). If Box2D ever adds edge or chain shapes, this will crash at render time.

### `interphyre/render/pygame.py`
**Purpose**: `PygameRenderer` — real-time pygame window.
**Internal deps**: render/base, Box2D
**Issues**: Not fully read. Inferred to mirror OpenCVRenderer pattern. Pygame has display initialization requirements that may conflict with headless environments.

### `interphyre/render/video.py`
**Purpose**: `VideoRecorder` — records simulation to mp4/gif file.
**Issues**: Not fully read. Depends on OpenCV's VideoWriter backend availability.

### `interphyre/render/__init__.py`
**Purpose**: Re-exports all renderers plus `save_obs_as_image()` utility.
**Public API**: `COLORS`, `DISCRETE_COLORS`, `RGB_TO_DISCRETE`, `Renderer`, `OpenCVRenderer`, `PygameRenderer`, `VideoRecorder`, `save_obs_as_image()`
**Issues**: `save_obs_as_image()` creates and immediately closes an `OpenCVRenderer` just to call `discrete_to_rgb()` — the renderer instance is not needed for RGB observations.

---

## Viewer

### `interphyre/viewer/_viewer.py`
**Purpose**: CLI tool for visualizing levels and actions; supports video recording.
**Public API**: `visualize_action()`, `run_demo()`
**Issues**: Not fully read. Hardcodes 600×600 / ppm=60 for video recording.

---

## Agents

### `agents/random_agent.py`
**Purpose**: `RandomAgent` — samples uniformly from action space with bounds clamping.
**Public API**: `set_action_space()`, `get_action(obs)`, `set_seed()`, `reset()`
**Issues**:
- `set_seed()` recreates `self.rng` but `action_space.sample()` (line 45) uses the action space's own internal RNG (set when the space was created), not `self.rng`. So `set_seed()` does not fully control the agent's randomness.
- The `self.rng` attribute is never used — the agent constructs an RNG but all sampling goes through `action_space.sample()`.

### `agents/evaluation.py`
**Purpose**: `Evaluator`, `EpisodeResult`, `EvaluationMetrics` — evaluation harness.
**Issues**: Not read; inferred from imports.

---

## Tools

### `tools/collect_data.py`
**Purpose**: Full data collection pipeline for generating `(scene, action, outcome)` datasets. Supports random and CEM agents, parallel workers, success/failure pair collection.
**Public API**: CLI script with `--level`, `--seeds`, `--agent`, `--workers` flags.
**Issues**:
- **Critical bug**: `DataCollector._create_env()` at line 371 calls `InterphyreEnv(level=level, config=self.config, ...)`. The first parameter of `InterphyreEnv.__init__` is `level_name: str`, not `level`. Passing `level=level` (a `Level` object) as a keyword argument will raise `TypeError: __init__() got an unexpected keyword argument 'level'`. This bug makes the data collection script non-functional as written. The correct call would use `InterphyreEnv.from_level(level, config=self.config, ...)`.
- Same bug in `DataCollector._verify_action()` at line 483: `InterphyreEnv(level=level, config=self.config, ...)`.
- `DataCollector._evaluate_action()` calls `self.env.reset(seed=seed)` inside the evaluation loop (line 466). This re-seeds the environment's numpy RNG but does not re-build the level (the level layout is fixed at construction). This is correct for replay but confusing — the `seed` argument to `env.reset()` only affects `env.np_random`, not the Box2D world state.
- The `CEMAgent.get_action()` raises `ValueError("CEM did not find a successful action")` (line 115) if no success is found after all iterations. This exception propagates to the `collect_seed` loop which catches it silently (line 443: `except Exception: continue`). The CEM agent is designed for finding successes, not failures — using `failure_agent = RandomAgent(seed=seed)` for failures is correct.

### `tools/benchmark_random_agent.py`
**Purpose**: Benchmarks the random agent across levels.
**Issues**: Not fully read.

---

## Demos

### `demos/quickstart.py`
**Purpose**: Minimal working example.
**Issues**: Passes `action = (0.5, 3.0, 0.6)` as a single tuple to `env.step()`. `step()` expects a list of tuples (for multi-action-object support) but also accepts a single tuple via the validation path. The docstring says "List of (x, y, size) tuples" but the example shows a bare tuple — this works but is inconsistent with the expected format.

### `demos/interventions.py`
**Purpose**: Demonstrates all intervention API methods.
**Issues**: All demos use `enable_interventions=True`. The `enable_interventions` flag does not actually gate trigger evaluation — any env can use `run_until()`/`restore()` but snapshot allocation is optimized away without the flag. Demo is accurate about the API.

### `demos/counterfactuals.py`
**Purpose**: Causal branching analysis via snapshot/restore.
**Issues**: Calls `env._step_physics()` (private method) directly in the factual/counterfactual branches. Using private methods in demos implies the public API lacks a supported single-step method — a gap.

### `demos/replanning.py`, `demos/triggers.py`, `demos/custom_levels.py`, `demos/gym_interface.py`
Not fully read. Inferred from filenames.

---

## Tests

### `tests/test_determinism.py`
**Purpose**: Verifies two engines with same seed produce identical body states after N steps.
**Issues**: Tests at engine level (bypasses `InterphyreEnv`). Does not test `StateSnapshot` round-trip determinism. Does not test determinism across machines (x86 vs ARM float rounding).

### Other test files
`test_all_levels.py`, `test_api_quality.py`, `test_benchmark_performance.py`, `test_edge_cases.py`, `test_engine.py`, `test_objects.py`, `test_performance.py`, `test_renderers.py`, `test_serialization.py`, `test_solution_validation.py`, `test_solutions.py`, `test_environment_additional.py`, `test_environment_validation.py`
**Issues**: Not fully read. Good breadth of test coverage based on filenames. `test_solutions.py` suggests solution validation tests exist; `test_serialization.py` likely covers StateSnapshot.

---

## Docs

### `docs/getting-started.md`
**Issues**: Accurate overall. "Running Demos" section suggests `for f in demos/*.py; do python $f; done` which will launch pygame windows without proper cleanup.

### `docs/api/environment.md`
**Issues**: Well-written. Does not document that `_step_physics()` is the only single-step method and is private. Does not document the `enable_interventions` flag's actual effect (vs. implied effect from the name). Does not document the `_active_interventions` reset option (which appears to be dead code anyway).

### `docs/api/` (other files)
Not fully read: `config.md`, `engine.md`, `interventions.md`, `level.md`, `levels.md`, `objects.md`, `render.md`

### General Docs Issues
- No documentation of the LLM tool-call workflow anywhere in `docs/`. This is the primary research use case but has zero coverage.
- No documentation of how to generate counterfactual datasets or trajectory traces.
- `docs/tools.md` presumably covers the viewer CLI; not read.

---

## Package Configuration

### `setup.py`
**Purpose**: Package metadata and dependencies.
**Issues**:
- `install_requires` pins `numpy>=1.26.0,<2.0.0` — excludes numpy 2.x. This is a restrictive pin that may conflict with newer torch versions.
- `packages=find_packages(exclude=["tests", "tools", "demos", "reference", "agents"])` — `agents/` is excluded from the package, meaning users who install via pip cannot import `agents`. The `tools/collect_data.py` imports from `agents` with a `sys.path.insert` workaround.

### `pyproject.toml`
**Purpose**: Ruff configuration only.
**Issues**: `tools/*` ignores `E402` (module-level imports not at top of file) — necessary because tools use `sys.path.insert` workarounds. This pattern could be eliminated if `agents/` were included in the package.

---

## Cross-Reference Summary of Critical Issues

| Issue | Location | Severity |
|-------|----------|----------|
| `collect_data.py` passes `level=` kwarg to `InterphyreEnv` (which takes `level_name`) | `tools/collect_data.py:370,483` | Bug — makes data collection non-functional |
| `_distance_ball_to_bar` uses `bar_obj` (initial state) not body position | `interphyre/engine.py:964` | Bug — contact validation wrong for dynamic bars |
| `contact_events` log is only populated when profiler is enabled | `interphyre/engine.py:95` | API gap — research methods silently return empty |
| `_hash_level` excludes object dimensions (radius, length) | `interphyre/interventions/state.py:348` | Bug — hash collision possible for geometrically different levels |
| `segmented_walls` is dead code in `create_basket` | `interphyre/objects/basket.py:79` | Dead code |
| `_active_interventions` populated but never consumed | `interphyre/environment.py:862` | Dead code |
| `RandomAgent.rng` never used — sampling goes through gym space | `agents/random_agent.py:45` | Latent seeding issue |
| No `place_action()` separate from `step()` | `interphyre/environment.py` | API gap for partial simulation |
| No text scene description method | `interphyre/level.py` | Gap for LLM tool-call use |
| `_update_relevant_contacts` uses color-based heuristic | `interphyre/engine.py:383` | Missing contacts in non-green-based success conditions |
| Pickle serialization in StateSnapshot | `interphyre/interventions/state.py:165` | Fragility/security |
