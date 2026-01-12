"""
Multi-turn simulation and replanning utilities.

This module provides high-level functions for interactive agents that need to
pause, observe, and replan during simulation.

Three main patterns are provided:
    - run_until: Simple explicit control for single pause points
    - SimulationIterator: Stateful iteration for complex multi-turn scenarios
    - simulate_with_breaks: Generator pattern for event-driven processing

Example:
    >>> from interphyre.interventions import run_until, on_contact
    >>>
    >>> snapshot, step = run_until(engine, on_contact("ball", "wall"))
    >>> if snapshot:
    ...     snapshot.restore(engine)
    ...     apply_intervention(engine)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Generator

if TYPE_CHECKING:
    from interphyre.engine import Box2DEngine
    from interphyre.interventions.state import StateSnapshot
    from interphyre.interventions.triggers import Trigger
    from interphyre.interventions.core import Intervention


def step_engine(engine: "Box2DEngine") -> None:
    """Execute a single physics step."""
    engine.world.Step(
        engine.config.time_step,
        engine.config.velocity_iters,
        engine.config.position_iters,
    )
    engine.time_update(engine.config.time_step)


def run_until(
    engine: "Box2DEngine",
    trigger: "Trigger",
    max_steps: int = 240,
    start_step: int = 0,
) -> tuple["StateSnapshot | None", int]:
    """
    Run simulation until trigger fires.

    Args:
        engine: Box2DEngine instance
        trigger: Trigger to wait for
        max_steps: Maximum steps to simulate
        start_step: Starting step index (for continuing after pause)

    Returns:
        (snapshot, step_index) if triggered, (None, final_step) if timeout

    Example:
        >>> snapshot, step = run_until(engine, on_contact("ball", "wall"))
        >>> if snapshot:
        ...     snapshot.restore(engine)
        ...     apply_intervention(engine)
        ...     snapshot2, step2 = run_until(engine, on_success(), start_step=step)
    """
    from interphyre.interventions.state import StateSnapshot

    for step_index in range(start_step, start_step + max_steps):
        step_engine(engine)
        if trigger.should_fire(step_index + 1, engine):
            return StateSnapshot.capture(
                engine, metadata={"step_index": step_index + 1, "trigger": str(trigger)}
            ), step_index + 1

    return None, start_step + max_steps


class SimulationIterator:
    """
    Stateful iterator for multi-break simulations with replanning.

    Attributes:
        engine: Box2DEngine instance
        triggers: List of triggers to monitor
        max_steps: Maximum simulation steps
        current_step: Current step index
        metadata: Optional metadata dict

    Example:
        >>> sim = SimulationIterator(engine, [on_contact("ball", "wall")])
        >>> while sim.current_step < sim.max_steps:
        ...     trigger, snapshot = sim.run_until_next_trigger()
        ...     if trigger is None:
        ...         break
        ...     snapshot.restore(engine)
        ...     apply_intervention(engine)
    """

    def __init__(
        self,
        engine: "Box2DEngine",
        triggers: list["Trigger"],
        max_steps: int = 500,
        metadata: dict[str, Any] | None = None,
    ):
        self.engine = engine
        self.triggers = triggers
        self.max_steps = max_steps
        self.current_step = 0
        self.metadata = metadata or {}
        self._trigger_history: list[tuple[int, "Trigger"]] = []

    def run_until_next_trigger(self) -> tuple["Trigger | None", "StateSnapshot | None"]:
        """
        Run until any trigger fires.

        Returns:
            (trigger, snapshot) if triggered, (None, None) if timeout
        """
        from interphyre.interventions.state import StateSnapshot

        while self.current_step < self.max_steps:
            step_engine(self.engine)
            self.current_step += 1

            for trigger in self.triggers:
                if trigger.should_fire(self.current_step, self.engine):
                    snapshot = StateSnapshot.capture(
                        self.engine,
                        metadata={
                            "step_index": self.current_step,
                            "trigger": str(trigger),
                            "trigger_index": self.triggers.index(trigger),
                        },
                    )
                    self._trigger_history.append((self.current_step, trigger))
                    return trigger, snapshot

        return None, None

    def get_trigger_history(self) -> list[tuple[int, "Trigger"]]:
        """Get history of all triggers that have fired."""
        return self._trigger_history.copy()

    def reset_triggers(self) -> None:
        """Reset all triggers to initial state."""
        for trigger in self.triggers:
            trigger.reset()


def simulate_with_breaks(
    engine: "Box2DEngine",
    triggers: list["Trigger"],
    max_steps: int = 500,
) -> Generator[tuple[int, "Trigger", "StateSnapshot"], None, None]:
    """
    Generator that yields (step, trigger, snapshot) when triggers fire.

    Args:
        engine: Box2DEngine instance
        triggers: List of triggers to monitor
        max_steps: Maximum simulation steps

    Yields:
        (step_index, trigger, snapshot) tuples when triggers fire

    Example:
        >>> for step, trigger, snapshot in simulate_with_breaks(engine, triggers):
        ...     if should_intervene(snapshot):
        ...         snapshot.restore(engine)
        ...         apply_intervention(engine)
    """
    from interphyre.interventions.state import StateSnapshot

    for step_index in range(max_steps):
        step_engine(engine)

        for trigger in triggers:
            if trigger.should_fire(step_index + 1, engine):
                snapshot = StateSnapshot.capture(
                    engine,
                    metadata={
                        "step_index": step_index + 1,
                        "trigger": str(trigger),
                        "trigger_index": triggers.index(trigger),
                    },
                )
                yield step_index + 1, trigger, snapshot
                break


@dataclass
class BranchResult:
    """
    Result from a single branch execution.

    Attributes:
        snapshot: Starting snapshot for this branch
        intervention: Intervention applied (None for factual)
        success: Whether success condition was met
        final_step: Final step index
        metadata: Additional metadata
    """

    snapshot: "StateSnapshot"
    intervention: "Intervention | None"
    success: bool
    final_step: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def causal_effect(self, baseline: "BranchResult") -> float:
        """Compute causal effect relative to baseline."""
        return float(self.success) - float(baseline.success)


def branch_and_compare(
    snapshot: "StateSnapshot",
    interventions: list["Intervention | Callable"],
    steps: int,
    include_factual: bool = True,
) -> list[BranchResult]:
    """
    Execute multiple branches from a snapshot and compare results.

    Args:
        snapshot: Starting snapshot
        interventions: List of interventions to try
        steps: Steps to simulate each branch
        include_factual: If True, include baseline branch with no intervention

    Returns:
        List of BranchResult objects

    Example:
        >>> results = branch_and_compare(snapshot, [intervention1, intervention2], steps=120)
        >>> for i, result in enumerate(results):
        ...     print(f"Branch {i}: {'SUCCESS' if result.success else 'FAILURE'}")
    """
    from interphyre.interventions.branch import SimulationTrajectory
    from interphyre.interventions.core import CallableIntervention

    results = []
    engine = snapshot._engine

    if include_factual:
        factual = SimulationTrajectory(snapshot=snapshot, metadata={"branch": "factual"})
        factual.execute(engine, steps)
        results.append(
            BranchResult(
                snapshot=snapshot,
                intervention=None,
                success=engine.level.success_condition(engine),
                final_step=snapshot.step_index + steps,
                metadata={"branch": "factual"},
            )
        )

    for idx, intervention in enumerate(interventions):
        if callable(intervention) and not isinstance(intervention, CallableIntervention):
            intervention = CallableIntervention(intervention, name=f"intervention_{idx}")

        trajectory = SimulationTrajectory(
            snapshot=snapshot, metadata={"branch": f"counterfactual_{idx}"}
        )
        trajectory.apply_intervention(intervention)
        trajectory.execute(engine, steps)

        results.append(
            BranchResult(
                snapshot=snapshot,
                intervention=intervention,
                success=engine.level.success_condition(engine),
                final_step=snapshot.step_index + steps,
                metadata={"branch": f"counterfactual_{idx}", "intervention_index": idx},
            )
        )

    return results


@dataclass
class CriticalMoment:
    """
    A moment in simulation identified as potentially important.

    Attributes:
        step_index: Step when moment occurred
        snapshot: State snapshot at this moment
        reason: Why this moment is critical
        score: Importance score (higher = more critical)
        metadata: Additional metadata
    """

    step_index: int
    snapshot: "StateSnapshot"
    reason: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


def find_critical_moments(
    engine: "Box2DEngine",
    max_steps: int = 240,
    min_score: float = 0.5,
) -> list[CriticalMoment]:
    """
    Automatically detect critical moments in simulation.

    Critical moments are identified based on collisions, velocity changes,
    and objects approaching success regions.

    Args:
        engine: Box2DEngine instance
        max_steps: Maximum steps to simulate
        min_score: Minimum importance score to include

    Returns:
        List of CriticalMoment objects sorted by score (descending)

    Example:
        >>> moments = find_critical_moments(engine, max_steps=240)
        >>> for moment in moments[:3]:
        ...     print(f"Step {moment.step_index}: {moment.reason} (score={moment.score:.2f})")
    """
    from interphyre.interventions.state import StateSnapshot

    moments = []
    previous_velocities = {}

    for step_index in range(max_steps):
        step_engine(engine)

        if hasattr(engine, "contact_listener") and engine.contact_listener.contacts:
            for contact in engine.contact_listener.contacts:
                moments.append(
                    CriticalMoment(
                        step_index=step_index + 1,
                        snapshot=StateSnapshot.capture(engine),
                        reason=f"Contact: {list(contact)}",
                        score=0.9,
                        metadata={"type": "contact", "objects": list(contact)},
                    )
                )

        for name, body in engine.bodies.items():
            velocity = body.linearVelocity
            speed = (velocity.x**2 + velocity.y**2) ** 0.5

            if name in previous_velocities:
                prev_speed = previous_velocities[name]
                speed_change = abs(speed - prev_speed)

                if speed_change > 2.0:
                    moments.append(
                        CriticalMoment(
                            step_index=step_index + 1,
                            snapshot=StateSnapshot.capture(engine),
                            reason=f"Velocity change: {name} ({speed_change:.2f})",
                            score=min(speed_change / 5.0, 1.0) * 0.7,
                            metadata={
                                "type": "velocity_change",
                                "object": name,
                                "change": speed_change,
                            },
                        )
                    )

            previous_velocities[name] = speed

        if engine.level.success_condition(engine):
            moments.append(
                CriticalMoment(
                    step_index=step_index + 1,
                    snapshot=StateSnapshot.capture(engine),
                    reason="Success condition met",
                    score=1.0,
                    metadata={"type": "success"},
                )
            )
            break

    moments = [m for m in moments if m.score >= min_score]
    moments.sort(key=lambda m: m.score, reverse=True)

    return moments
