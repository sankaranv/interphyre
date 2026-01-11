"""
Experiment utilities for trial management and counterfactual analysis.

This module provides high-level utilities for running controlled experiments,
including trial management, counterfactual pair generation, and result aggregation.
"""

from typing import Callable, Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

from interphyre.interventions.state import StateSnapshot
from interphyre.interventions.core import Intervention


class AblationType(Enum):
    """
    Type of ablation to perform in ablation studies.

    Attributes:
        FREEZE: Set object velocities to zero (object remains in world)
        REMOVE: Remove object from the simulation entirely
    """
    FREEZE = "freeze"
    REMOVE = "remove"


@dataclass
class FactualCounterfactualPair:
    """
    Result pair from factual and counterfactual simulations.

    Attributes:
        snapshot: The snapshot where the timeline diverged
        factual_result: Result from simulation without intervention
        counterfactual_result: Result from simulation with intervention
        intervention: The intervention applied in counterfactual branch
        metadata: Optional metadata about the pair
    """

    snapshot: StateSnapshot
    factual_result: Dict[str, Any]
    counterfactual_result: Dict[str, Any]
    intervention: Optional[Intervention] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def causal_effect(self, outcome_key: str = "success") -> float:
        """
        Compute causal effect as difference in outcomes.

        Args:
            outcome_key: Key to compare in results (default: "success")

        Returns:
            Difference: counterfactual - factual
        """
        factual_value = self.factual_result.get(outcome_key, 0)
        cf_value = self.counterfactual_result.get(outcome_key, 0)
        return cf_value - factual_value


@dataclass
class ExperimentResults:
    """
    Aggregated results from multiple experimental trials.

    Attributes:
        trials: List of trial results
        metadata: Experiment-level metadata
    """

    trials: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_trial(self, result: Dict[str, Any]) -> None:
        """Add a trial result to the experiment."""
        self.trials.append(result)

    def get_mean(self, key: str) -> float:
        """
        Get mean value across trials for a specific key.

        Args:
            key: Result key to average

        Returns:
            Mean value across trials
        """
        values = [trial.get(key, 0) for trial in self.trials]
        return float(np.mean(values))

    def get_std(self, key: str) -> float:
        """
        Get standard deviation across trials for a specific key.

        Args:
            key: Result key

        Returns:
            Standard deviation across trials
        """
        values = [trial.get(key, 0) for trial in self.trials]
        return float(np.std(values))

    def get_success_rate(self) -> float:
        """
        Get success rate across trials.

        Returns:
            Proportion of successful trials
        """
        successes = sum(1 for trial in self.trials if trial.get("success", False))
        return successes / len(self.trials) if self.trials else 0.0

    def summary(self) -> Dict[str, Any]:
        """
        Get summary statistics across all trials.

        Returns:
            Dictionary with mean/std for numeric keys and success rate
        """
        if not self.trials:
            return {"num_trials": 0}

        summary_dict = {"num_trials": len(self.trials)}

        # Extract all numeric keys from first trial
        sample_trial = self.trials[0]
        for key in sample_trial:
            if isinstance(sample_trial[key], (int, float)):
                summary_dict[f"{key}_mean"] = self.get_mean(key)
                summary_dict[f"{key}_std"] = self.get_std(key)

        # Add success rate if available
        if any("success" in trial for trial in self.trials):
            summary_dict["success_rate"] = self.get_success_rate()

        return summary_dict


def generate_counterfactual_pairs(
    engine_factory: Callable[[], Any],
    intervention_step_index: int,
    interventions: List[Callable],
    simulation_steps: int,
    num_trials: int = 1,
    seed: Optional[int] = None,
) -> List[FactualCounterfactualPair]:
    """
    Generate multiple factual-counterfactual pairs for causal analysis.

    Args:
        engine_factory: Callable that returns a fresh engine instance
        intervention_step_index: Step index at which to apply intervention
        interventions: List of intervention functions
        simulation_steps: Total steps to simulate
        num_trials: Number of trials to run
        seed: Random seed for reproducibility

    Returns:
        List of FactualCounterfactualPair objects

    Example:
        def make_engine():
            from interphyre import Box2DEngine
            from interphyre.level import load_level
            level = load_level("two_body_problem")
            return Box2DEngine(level)

        def boost_velocity(engine):
            body = engine.bodies["green_ball"]
            body.linearVelocity = (body.linearVelocity.x * 1.5, body.linearVelocity.y * 1.5)

        pairs = generate_counterfactual_pairs(
            engine_factory=make_engine,
            intervention_step_index=50,
            interventions=[boost_velocity],
            simulation_steps=100,
            num_trials=10,
            seed=42
        )

        avg_effect = np.mean([p.causal_effect() for p in pairs])
    """
    if seed is not None:
        np.random.seed(seed)

    pairs = []

    for trial_idx in range(num_trials):
        # Create engine
        engine = engine_factory()

        # Run to intervention step
        for step in range(intervention_step_index):
            engine.world.Step(
                engine.config.time_step,
                engine.config.velocity_iters,
                engine.config.position_iters,
            )
            engine.time_update(engine.config.time_step)

        # Capture snapshot at intervention point
        snapshot = StateSnapshot.capture(engine)

        # Factual branch - continue without intervention
        for step in range(simulation_steps - intervention_step_index):
            engine.world.Step(
                engine.config.time_step,
                engine.config.velocity_iters,
                engine.config.position_iters,
            )
            engine.time_update(engine.config.time_step)

        step_count = int(
            round(engine.contact_listener.current_time / engine.config.time_step)
        )
        factual_result = {
            "success": engine.level.success_condition(engine),
            "step_count": step_count,
            "final_time": engine.contact_listener.current_time,
        }

        # Counterfactual branch - apply intervention and continue
        for intervention_fn in interventions:
            # Restore to snapshot
            snapshot.restore(engine)

            # Apply intervention
            intervention_fn(engine)

            # Continue simulation
            for step in range(simulation_steps - intervention_step_index):
                engine.world.Step(
                    engine.config.time_step,
                    engine.config.velocity_iters,
                    engine.config.position_iters,
                )
                engine.time_update(engine.config.time_step)

            step_count = int(
                round(engine.contact_listener.current_time / engine.config.time_step)
            )
            cf_result = {
                "success": engine.level.success_condition(engine),
                "step_count": step_count,
                "final_time": engine.contact_listener.current_time,
            }

            pairs.append(
                FactualCounterfactualPair(
                    snapshot=snapshot,
                    factual_result=factual_result,
                    counterfactual_result=cf_result,
                    metadata={
                        "trial_idx": trial_idx,
                        "intervention_step_index": intervention_step_index,
                        "simulation_steps": simulation_steps,
                    },
                )
            )

    return pairs


def run_ablation_study(
    engine_factory: Callable[[], Any],
    intervention_step_index: int,
    object_names: List[str],
    simulation_steps: int,
    ablation_type: Union[AblationType, str] = AblationType.FREEZE,
) -> Dict[str, ExperimentResults]:
    """
    Run ablation study by systematically removing/freezing objects.

    Args:
        engine_factory: Callable that returns a fresh engine instance
        intervention_step_index: Step index at which to ablate
        object_names: List of objects to ablate
        simulation_steps: Total steps to simulate
        ablation_type: Type of ablation (AblationType.FREEZE or AblationType.REMOVE, also accepts "freeze" or "remove" strings for backward compatibility)

    Returns:
        Dictionary mapping object names to experiment results

    Example:
        from interphyre.interventions import AblationType

        def make_engine():
            from interphyre import Box2DEngine
            from interphyre.level import load_level
            level = load_level("two_body_problem")
            return Box2DEngine(level)

        results = run_ablation_study(
            engine_factory=make_engine,
            intervention_step_index=30,
            object_names=["green_ball", "red_ball"],
            simulation_steps=100,
            ablation_type=AblationType.FREEZE
        )

        for obj_name, result in results.items():
            print(f"{obj_name} ablation success rate: {result.get_success_rate():.2%}")
    """
    # Convert string to enum for backward compatibility
    if isinstance(ablation_type, str):
        ablation_type = AblationType(ablation_type)
    ablation_results = {}

    for obj_name in object_names:
        # Create engine
        engine = engine_factory()

        # Run to intervention step
        for step in range(intervention_step_index):
            engine.world.Step(
                engine.config.time_step,
                engine.config.velocity_iters,
                engine.config.position_iters,
            )
            engine.time_update(engine.config.time_step)

        # Capture baseline result (no intervention)
        snapshot = StateSnapshot.capture(engine)
        for step in range(simulation_steps - intervention_step_index):
            engine.world.Step(
                engine.config.time_step,
                engine.config.velocity_iters,
                engine.config.position_iters,
            )
            engine.time_update(engine.config.time_step)
        baseline_success = engine.level.success_condition(engine)

        # Apply ablation
        snapshot.restore(engine)

        if ablation_type == AblationType.FREEZE:
            # Freeze object velocity
            body = engine.bodies.get(obj_name)
            if body:
                from Box2D import b2Vec2

                body.linearVelocity = b2Vec2(0, 0)
                body.angularVelocity = 0
        elif ablation_type == AblationType.REMOVE:
            # Remove object from world
            body = engine.bodies.get(obj_name)
            if body:
                engine.world.DestroyBody(body)
                del engine.bodies[obj_name]

        # Continue simulation
        for step in range(simulation_steps - intervention_step_index):
            engine.world.Step(
                engine.config.time_step,
                engine.config.velocity_iters,
                engine.config.position_iters,
            )
            engine.time_update(engine.config.time_step)

        ablated_success = engine.level.success_condition(engine)

        # Record results
        exp_results = ExperimentResults(
            trials=[
                {
                    "baseline_success": baseline_success,
                    "ablated_success": ablated_success,
                    "causal_effect": float(ablated_success) - float(baseline_success),
                }
            ],
            metadata={"object_name": obj_name, "ablation_type": ablation_type.value},
        )

        ablation_results[obj_name] = exp_results

    return ablation_results


def compare_interventions(
    engine_factory: Callable[[], Any],
    intervention_step_index: int,
    interventions: Dict[str, Callable],
    simulation_steps: int,
    num_trials: int = 10,
    seed: Optional[int] = None,
) -> Dict[str, ExperimentResults]:
    """
    Compare multiple interventions against baseline.

    Args:
        engine_factory: Callable that returns a fresh engine instance
        intervention_step_index: Step index at which to intervene
        interventions: Dictionary mapping intervention names to functions
        simulation_steps: Total steps to simulate
        num_trials: Number of trials per intervention
        seed: Random seed for reproducibility

    Returns:
        Dictionary mapping intervention names to experiment results

    Example:
        def make_engine():
            from interphyre import Box2DEngine
            from interphyre.level import load_level
            level = load_level("two_body_problem")
            return Box2DEngine(level)

        interventions = {
            "boost_green": lambda e: e.bodies["green_ball"].ApplyLinearImpulse((0, 5), e.bodies["green_ball"].worldCenter, True),
            "freeze_red": lambda e: setattr(e.bodies["red_ball"], "linearVelocity", (0, 0)),
        }

        results = compare_interventions(
            engine_factory=make_engine,
            intervention_step_index=50,
            interventions=interventions,
            simulation_steps=100,
            num_trials=10
        )
    """
    if seed is not None:
        np.random.seed(seed)

    comparison_results = {}

    # Run baseline (no intervention)
    baseline_results = ExperimentResults(metadata={"intervention": "baseline"})

    for trial in range(num_trials):
        engine = engine_factory()

        for step in range(simulation_steps):
            engine.world.Step(
                engine.config.time_step,
                engine.config.velocity_iters,
                engine.config.position_iters,
            )
            engine.time_update(engine.config.time_step)

        step_count = int(
            round(engine.contact_listener.current_time / engine.config.time_step)
        )
        baseline_results.add_trial(
            {
                "success": engine.level.success_condition(engine),
                "step_count": step_count,
            }
        )

    comparison_results["baseline"] = baseline_results

    # Run each intervention
    for intervention_name, intervention_fn in interventions.items():
        intervention_results = ExperimentResults(metadata={"intervention": intervention_name})

        for trial in range(num_trials):
            engine = engine_factory()

            # Run to intervention step
            for step in range(intervention_step_index):
                engine.world.Step(
                    engine.config.time_step,
                    engine.config.velocity_iters,
                    engine.config.position_iters,
                )
                engine.time_update(engine.config.time_step)

            # Apply intervention
            intervention_fn(engine)

            # Continue simulation
            for step in range(simulation_steps - intervention_step_index):
                engine.world.Step(
                    engine.config.time_step,
                    engine.config.velocity_iters,
                    engine.config.position_iters,
                )
                engine.time_update(engine.config.time_step)

            step_count = int(
                round(engine.contact_listener.current_time / engine.config.time_step)
            )
            intervention_results.add_trial(
                {
                    "success": engine.level.success_condition(engine),
                    "step_count": step_count,
                }
            )

        comparison_results[intervention_name] = intervention_results

    return comparison_results
