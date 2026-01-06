"""
Simulation branching for counterfactual analysis.

This module provides the SimulationBranch class for managing timeline branches
from snapshots, enabling clean factual/counterfactual pair generation for causal
inference experiments.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from interphyre.interventions.state import StateSnapshot

if TYPE_CHECKING:
    from interphyre.engine import Box2DEngine
    from interphyre.interventions.core import Intervention


@dataclass
class SimulationBranch:
    """
    Represents a branch from a snapshot with optional interventions.

    A branch captures a divergence point in the simulation timeline,
    allowing execution of counterfactual scenarios while preserving
    the original factual timeline.

    Attributes:
        snapshot: The state snapshot this branch starts from
        parent_branch: Optional parent branch (for nested counterfactuals)
        interventions: List of interventions to apply in this branch
        branch_id: Unique identifier for this branch
        metadata: User-provided metadata for experimental tracking
    """

    snapshot: StateSnapshot
    parent_branch: Optional["SimulationBranch"] = None
    interventions: List["Intervention"] = field(default_factory=list)
    branch_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def apply_intervention(self, intervention: "Intervention") -> None:
        """
        Add an intervention to this branch.

        The intervention will be applied when the branch is executed.

        Args:
            intervention: The intervention to apply
        """
        self.interventions.append(intervention)

    def execute(
        self, engine: "Box2DEngine", steps: int, return_trace: bool = False
    ) -> Dict[str, Any]:
        """
        Execute this branch for the specified number of steps.

        This restores the snapshot, applies all interventions, then runs
        the simulation forward.

        Args:
            engine: The Box2DEngine to execute on
            steps: Number of simulation steps to run
            return_trace: If True, return full trajectory; else just final state

        Returns:
            Dictionary containing:
                - branch_id: Unique identifier for this branch
                - final_snapshot: StateSnapshot at the end of execution
                - trace: List of snapshots at each step (if return_trace=True)
                - metadata: Branch metadata
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
            "branch_id": self.branch_id,
            "final_snapshot": final_snapshot,
            "metadata": self.metadata,
        }

        if return_trace:
            result["trace"] = trace

        return result

    def create_child_branch(
        self, snapshot: Optional[StateSnapshot] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> "SimulationBranch":
        """
        Create a child branch from this branch.

        This enables nested counterfactuals where you branch from a branch.

        Args:
            snapshot: Snapshot to branch from (default: this branch's snapshot)
            metadata: Metadata for the child branch

        Returns:
            New SimulationBranch with this branch as parent
        """
        if snapshot is None:
            snapshot = self.snapshot

        return SimulationBranch(
            snapshot=snapshot,
            parent_branch=self,
            metadata=metadata or {},
        )

    def get_ancestry(self) -> List["SimulationBranch"]:
        """
        Get the ancestry chain of this branch.

        Returns:
            List of branches from root to this branch (inclusive)
        """
        ancestry = []
        current = self
        while current is not None:
            ancestry.append(current)
            current = current.parent_branch
        return list(reversed(ancestry))

    def __repr__(self) -> str:
        parent_id = self.parent_branch.branch_id[:8] if self.parent_branch else "None"
        return (
            f"SimulationBranch(id={self.branch_id[:8]}, "
            f"parent={parent_id}, "
            f"interventions={len(self.interventions)}, "
            f"step={self.snapshot.step_count})"
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
    Convenience function to create and execute a factual/counterfactual pair.

    This is a common pattern in causal inference: compare outcomes with and
    without an intervention from the same starting state.

    Args:
        engine: The Box2DEngine to execute on
        snapshot: The snapshot to branch from
        counterfactual_interventions: List of interventions for counterfactual
        steps: Number of steps to run each branch
        factual_metadata: Metadata for factual branch
        counterfactual_metadata: Metadata for counterfactual branch

    Returns:
        Tuple of (factual_result, counterfactual_result)
    """
    # Factual branch (no interventions)
    factual_branch = SimulationBranch(
        snapshot=snapshot,
        metadata=factual_metadata or {"condition": "factual"},
    )
    factual_result = factual_branch.execute(engine, steps)

    # Counterfactual branch (with interventions)
    counterfactual_branch = SimulationBranch(
        snapshot=snapshot,
        metadata=counterfactual_metadata or {"condition": "counterfactual"},
    )
    for intervention in counterfactual_interventions:
        counterfactual_branch.apply_intervention(intervention)
    counterfactual_result = counterfactual_branch.execute(engine, steps)

    return factual_result, counterfactual_result
