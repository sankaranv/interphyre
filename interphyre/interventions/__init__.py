"""
Interventions API for Interphyre PHYRE Simulator.

This module provides a comprehensive toolkit for interventions in physics simulations,
optimized for causal inference, mechanistic interpretability, and interactive experiments.

## Quick Start

Basic state capture and restoration:
    from interphyre import Box2DEngine
    from interphyre.levels import load_level
    from interphyre.config import SimulationConfig
    from interphyre.interventions import StateSnapshot

    level = load_level("two_body_problem")
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    # Capture state
    snapshot = StateSnapshot.capture(engine)

    # Run simulation...
    for _ in range(100):
        engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
        engine.time_update(config.time_step)

    # Restore to exact state
    snapshot.restore(engine)

Apply interventions with context manager:
    from interphyre.interventions import InterventionContext

    with InterventionContext(engine) as ctx:
        ctx.set_position("green_ball", x=2.0, y=3.0)
        ctx.set_velocity("green_ball", vx=1.0, vy=-1.0)
        ctx.scale_velocity("red_ball", factor=1.5)

Schedule automated interventions:
    from interphyre.interventions import InterventionScheduler, at_step, on_contact

    scheduler = InterventionScheduler(engine)
    engine.attach_intervention_scheduler(scheduler)

    # At step 50, boost velocity
    scheduler.add(
        trigger=at_step(50),
        intervention=lambda e: e.bodies["ball"].ApplyLinearImpulse((0, 10), e.bodies["ball"].worldCenter, True)
    )

    # When objects contact, freeze simulation
    scheduler.add(
        trigger=on_contact("green_ball", "red_ball", once_only=True),
        intervention=lambda e: setattr(e.bodies["green_ball"], "linearVelocity", (0, 0))
    )

Generate counterfactual pairs:
    from interphyre.interventions import generate_counterfactual_pairs

    def boost_velocity(engine):
        body = engine.bodies["green_ball"]
        body.linearVelocity = (body.linearVelocity.x * 1.5, body.linearVelocity.y * 1.5)

    pairs = generate_counterfactual_pairs(
        engine_factory=lambda: Box2DEngine(load_level("two_body_problem")),
        intervention_step=50,
        interventions=[boost_velocity],
        simulation_steps=200,
        num_trials=10
    )

    # Analyze causal effects
    effects = [p.causal_effect("success") for p in pairs]

## API Organization

**Core State Management:**
- `StateSnapshot` - Capture and restore complete simulation state
- `Intervention` - Base class for custom interventions
- `CallableIntervention` - Wrap functions as interventions

**Trajectory & Simulation:**
- `SimulationTrajectory` - Manage diverging simulation trajectories
- `create_factual_counterfactual_pair` - Quick factual/counterfactual comparison

**Scheduling System:**
- `InterventionScheduler` - Automated intervention execution
- Triggers: `at_step`, `on_contact`, `on_contact_with`, `on_success`, `when`

**Context Manager API:**
- `InterventionContext` - Apply interventions with automatic rollback
- Helper methods: `set_position`, `set_velocity`, `scale_velocity`, `set_angle`,
  `set_angular_velocity`, `set_gravity`, `apply_impulse`, `freeze`

**Experiment Utilities:**
- `ExperimentResults` - Statistical aggregation of trial results
- `generate_counterfactual_pairs` - Automated factual/counterfactual generation
- `run_ablation_study` - Systematic object removal analysis
- `compare_interventions` - Multi-intervention comparison
- `FactualCounterfactualPair` - Structured result pair for causal analysis

## Best Practices

1. **Enable interventions in config:**
   config = SimulationConfig(enable_interventions=True)

2. **Use InterventionContext for safety:**
   - Automatically captures snapshot on entry
   - Rolls back on exception (with auto_rollback=True)
   - Tracks all modifications for reproducibility

3. **Use InterventionContext as a context manager:**
   with InterventionContext(engine) as ctx:
       ctx.set_velocity("ball", vx=2.0)

   # For counterfactual analysis (no rollback on exception)
   with InterventionContext(engine, auto_rollback=False) as ctx:
       ctx.set_velocity("ball", vx=2.0)

4. **Chain methods for multiple modifications:**
   with InterventionContext(engine) as ctx:
       ctx.set_position("ball", x=1.0, y=2.0).set_velocity("ball", vx=3.0, vy=4.0)

5. **Use experiment utilities for systematic analysis:**
   - generate_counterfactual_pairs() for causal inference
   - run_ablation_study() for feature importance
   - compare_interventions() for strategy evaluation
"""

from interphyre.interventions.state import StateSnapshot
from interphyre.interventions.branch import (
    SimulationTrajectory,
    create_factual_counterfactual_pair,
)

from interphyre.interventions.scheduler import InterventionScheduler
from interphyre.interventions.triggers import (
    Trigger,
    TimeBasedTrigger,
    EventBasedTrigger,
    ConditionBasedTrigger,
    at_step,
    on_contact,
    on_contact_with,
    on_success,
    when,
)

from interphyre.interventions.core import (
    Intervention,
    CallableIntervention,
)
from interphyre.interventions.api import InterventionContext
from interphyre.interventions.experiments import (
    FactualCounterfactualPair,
    ExperimentResults,
    AblationType,
    generate_counterfactual_pairs,
    run_ablation_study,
    compare_interventions,
)

__all__ = [
    # Core state management
    "StateSnapshot",
    # Base intervention classes
    "Intervention",
    "CallableIntervention",
    # Trajectory and simulation
    "SimulationTrajectory",
    "create_factual_counterfactual_pair",
    # Scheduling
    "InterventionScheduler",
    "Trigger",
    "TimeBasedTrigger",
    "EventBasedTrigger",
    "ConditionBasedTrigger",
    "at_step",
    "on_contact",
    "on_contact_with",
    "on_success",
    "when",
    # Context manager API
    "InterventionContext",
    # Experiment utilities
    "FactualCounterfactualPair",
    "ExperimentResults",
    "AblationType",
    "generate_counterfactual_pairs",
    "run_ablation_study",
    "compare_interventions",
]
