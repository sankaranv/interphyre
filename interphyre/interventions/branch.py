"""
Simulation trajectories for counterfactual analysis.

This module provides the SimulationTrajectory class for managing diverging simulation
trajectories from snapshots, enabling clean factual/counterfactual pair generation
for causal inference experiments.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from interphyre.interventions.state import StateSnapshot

if TYPE_CHECKING:
    from interphyre.engine import Box2DEngine
    from interphyre.interventions.core import Intervention


@dataclass
class SimulationTrajectory:
    """
    Represents a simulation trajectory from a snapshot with optional interventions.

    A trajectory captures a divergence point in the simulation, allowing execution
    of counterfactual scenarios while preserving the original factual timeline.
    This is useful for causal inference and "what-if" analysis.

    Attributes:
        snapshot: The state snapshot this trajectory starts from
        parent_trajectory: Optional parent trajectory (for nested counterfactuals)
        interventions: List of interventions to apply in this trajectory
        trajectory_id: Unique identifier for this trajectory
        metadata: User-provided metadata for experimental tracking
    """

    snapshot: StateSnapshot
    parent_trajectory: Optional["SimulationTrajectory"] = None
    interventions: List["Intervention"] = field(default_factory=list)
    trajectory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def apply_intervention(self, intervention: "Intervention") -> None:
        """
        Add an intervention to this trajectory.

        The intervention will be applied when the trajectory is executed.

        Args:
            intervention: The intervention to apply
        """
        self.interventions.append(intervention)

    def execute(
        self, engine: "Box2DEngine", steps: int, return_trace: bool = False
    ) -> Dict[str, Any]:
        """
        Execute this trajectory for the specified number of steps.

        This restores the snapshot, applies all interventions, then runs
        the simulation forward.

        Args:
            engine: The Box2DEngine to execute on
            steps: Number of simulation steps to run
            return_trace: If True, return full trace of snapshots; else just final state

        Returns:
            Dictionary containing:
                - trajectory_id: Unique identifier for this trajectory
                - final_snapshot: StateSnapshot at the end of execution
                - trace: List of snapshots at each step (if return_trace=True)
                - metadata: Trajectory metadata
        """
        # Restore to snapshot state
        self.snapshot.restore(engine)

        # Apply all interventions
        for intervention in self.interventions:
            intervention.apply(engine)

        # Run simulation
        trace = []
        if return_trace:
            trace.append(StateSnapshot.capture(engine))

        for _ in range(steps):
            engine.world.Step(
                engine.config.time_step,
                engine.config.velocity_iters,
                engine.config.position_iters,
            )
            engine.time_update(engine.config.time_step)

            if return_trace:
                trace.append(StateSnapshot.capture(engine))

        # Capture final state
        final_snapshot = StateSnapshot.capture(engine)

        result = {
            "trajectory_id": self.trajectory_id,
            "final_snapshot": final_snapshot,
            "metadata": self.metadata,
        }

        if return_trace:
            result["trace"] = trace

        return result

    def create_child_trajectory(
        self, snapshot: Optional[StateSnapshot] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> "SimulationTrajectory":
        """
        Create a child trajectory from this trajectory.

        This enables nested counterfactuals where you create diverging
        timelines from an already diverged timeline.

        Args:
            snapshot: Snapshot to start from (default: this trajectory's snapshot)
            metadata: Metadata for the child trajectory

        Returns:
            New SimulationTrajectory with this trajectory as parent
        """
        if snapshot is None:
            snapshot = self.snapshot

        return SimulationTrajectory(
            snapshot=snapshot,
            parent_trajectory=self,
            metadata=metadata or {},
        )

    def get_ancestry(self) -> List["SimulationTrajectory"]:
        """
        Get the ancestry chain of this trajectory.

        Returns:
            List of trajectories from root to this trajectory (inclusive)
        """
        ancestry = []
        current = self
        while current is not None:
            ancestry.append(current)
            current = current.parent_trajectory
        return list(reversed(ancestry))

    def __repr__(self) -> str:
        parent_id = self.parent_trajectory.trajectory_id[:8] if self.parent_trajectory else "None"
        return (
            f"SimulationTrajectory(id={self.trajectory_id[:8]}, "
            f"parent={parent_id}, "
            f"interventions={len(self.interventions)}, "
            f"step={self.snapshot.step_index})"
        )


def create_factual_counterfactual_pair(
    engine: "Box2DEngine",
    snapshot: StateSnapshot,
    counterfactual_interventions: List["Intervention"],
    steps: int,
    factual_metadata: Optional[Dict[str, Any]] = None,
    counterfactual_metadata: Optional[Dict[str, Any]] = None,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Convenience function to create and execute a factual/counterfactual trajectory pair.

    This is a common pattern in causal inference: compare outcomes with and
    without an intervention from the same starting state.

    Args:
        engine: The Box2DEngine to execute on
        snapshot: The snapshot to start from
        counterfactual_interventions: List of interventions for counterfactual trajectory
        steps: Number of steps to run each trajectory
        factual_metadata: Metadata for factual trajectory
        counterfactual_metadata: Metadata for counterfactual trajectory

    Returns:
        Tuple of (factual_result, counterfactual_result)
    """
    # Factual trajectory (no interventions)
    factual_trajectory = SimulationTrajectory(
        snapshot=snapshot,
        metadata=factual_metadata or {"condition": "factual"},
    )
    factual_result = factual_trajectory.execute(engine, steps)

    # Counterfactual trajectory (with interventions)
    counterfactual_trajectory = SimulationTrajectory(
        snapshot=snapshot,
        metadata=counterfactual_metadata or {"condition": "counterfactual"},
    )
    for intervention in counterfactual_interventions:
        counterfactual_trajectory.apply_intervention(intervention)
    counterfactual_result = counterfactual_trajectory.execute(engine, steps)

    return factual_result, counterfactual_result
