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

from interphyre.interventions.state import StateSnapshot
from interphyre.interventions.branch import (
    SimulationBranch,
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

from interphyre.interventions.api import (
    InterventionContext,
    with_intervention,
    counterfactual_intervention,
)
from interphyre.interventions.experiments import (
    FactualCounterfactualPair,
    ExperimentResults,
    generate_counterfactual_pairs,
    run_ablation_study,
    compare_interventions,
)

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
    "InterventionContext",
    "with_intervention",
    "counterfactual_intervention",
    "FactualCounterfactualPair",
    "ExperimentResults",
    "generate_counterfactual_pairs",
    "run_ablation_study",
    "compare_interventions",
]
