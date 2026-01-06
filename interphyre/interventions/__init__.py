"""
Interventions API for Interphyre PHYRE Simulator.

This module provides capabilities for:
- State capture and restoration (snapshots)
- Branching simulations for counterfactual analysis
- Time/event/condition-based intervention scheduling
- Clean experimental design for causal inference

Example usage:
    from interphyre import PhyreEnv
    from interphyre.interventions import StateSnapshot

    env = PhyreEnv(level, config=SimulationConfig(enable_interventions=True))
    obs, info = env.reset()
    env.step(action)

    # Capture state at any point
    snapshot = StateSnapshot.capture(env.engine)

    # Continue simulation
    for _ in range(50):
        env.engine.world.Step(...)

    # Restore to captured state - exact deterministic replay
    snapshot.restore(env.engine)
"""

# Phase 1: Core State Capture & Restoration
from interphyre.interventions.state import StateSnapshot

# Phase 2: Branching Simulations
from interphyre.interventions.branch import (
    SimulationBranch,
    create_factual_counterfactual_pair,
)

# Phase 3: Time/Event/Condition-Based Interventions
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

# Future phases will add:
# from interphyre.interventions.api import with_intervention, counterfactual_pair

__all__ = [
    "StateSnapshot",
    "SimulationBranch",
    "create_factual_counterfactual_pair",
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
]

__version__ = "0.1.0"
