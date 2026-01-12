# Interventions

Interventions allow controlled edits to the simulation state, supporting counterfactual analysis and causal experiments.

## Core types

- `Intervention`: abstract base class with `apply(engine)`.
- `CallableIntervention`: wraps a callable as an `Intervention`.

## Context manager API

`InterventionContext` provides a safe, fluent interface and automatic rollback on exceptions.

```python
from interphyre.interventions import InterventionContext

with InterventionContext(engine) as ctx:
    ctx.set_position("green_ball", x=2.0, y=3.0)
    ctx.set_velocity("red_ball", vx=0.0, vy=-1.0)
```

Notable methods:

- `set_position`, `set_velocity`, `scale_velocity`
- `set_angle`, `set_angular_velocity`
- `set_gravity`, `apply_impulse`, `freeze`

## Triggers

Triggers decide when an intervention should fire:

- `TimeBasedTrigger` / `at_step(step)`
- `EventBasedTrigger` / `on_contact(a, b)` / `on_contact_with(obj)`
- `ConditionBasedTrigger` / `when(condition)`
- `on_success()` for success-condition events

## Scheduling

`InterventionScheduler` executes scheduled interventions during engine stepping.

```python
from interphyre.interventions import InterventionScheduler, at_step
scheduler = InterventionScheduler(engine)
scheduler.add(at_step(50), CallableIntervention(lambda e: ...))
```

## State snapshots and branching

- `StateSnapshot.capture(engine)` and `.restore(engine)` for deterministic rollback.
- `SimulationBranch` to execute a branch with interventions.
- `create_factual_counterfactual_pair` helper for paired runs.

## Experiment utilities

- `generate_counterfactual_pairs`
- `run_ablation_study`
- `compare_interventions`
- `ExperimentResults`, `FactualCounterfactualPair`
