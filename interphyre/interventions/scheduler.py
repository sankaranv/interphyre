"""
Intervention scheduler for automated intervention execution.

This module provides the InterventionScheduler class that manages scheduled
interventions during simulation, checking triggers and executing interventions
at the appropriate times.
"""

from typing import List, Tuple, TYPE_CHECKING

from interphyre.interventions.triggers import Trigger
from interphyre.interventions.core import Intervention

if TYPE_CHECKING:
    from interphyre.engine import Box2DEngine


class InterventionScheduler:
    """
    Manages scheduled interventions during simulation.

    The scheduler maintains a list of (trigger, intervention) pairs and checks
    each trigger every simulation step. When a trigger fires, its associated
    intervention is executed.

    Attributes:
        engine: The Box2DEngine being scheduled
        pending: List of pending (trigger, intervention) pairs
        executed: List of executed (step, intervention) pairs
        enabled: Whether the scheduler is currently active
    """

    def __init__(self, engine: "Box2DEngine"):
        """
        Initialize the intervention scheduler.

        Args:
            engine: The Box2DEngine to schedule interventions for
        """
        self.engine = engine
        self.pending: List[Tuple[Trigger, Intervention]] = []
        self.executed: List[Tuple[int, Intervention]] = []
        self.enabled = True

    def add(self, trigger: Trigger, intervention: Intervention) -> None:
        """
        Schedule an intervention to be executed when trigger fires.

        Args:
            trigger: The trigger that determines when to execute
            intervention: The intervention to execute
        """
        self.pending.append((trigger, intervention))
        # Sort by priority (lower = earlier)
        self.pending.sort(key=lambda x: x[0].priority)

    def check_triggers(self, step_idx: int, engine: "Box2DEngine") -> None:
        """
        Check all pending triggers and execute interventions that should fire.

        This is called each simulation step by the engine.

        Args:
            step_idx: Current simulation step index
            engine: The Box2DEngine being simulated
        """
        if not self.enabled:
            return

        to_execute = []
        remaining = []

        # Check each pending trigger
        for trigger, intervention in self.pending:
            if trigger.should_fire(step_idx, engine):
                to_execute.append((trigger, intervention))
            else:
                remaining.append((trigger, intervention))

        # Update pending list (remove fired triggers if they were once-only)
        self.pending = remaining

        # Execute interventions in priority order
        for trigger, intervention in to_execute:
            intervention.apply(engine)
            self.executed.append((step_idx, intervention))

    def clear(self) -> None:
        """Clear all pending interventions."""
        self.pending.clear()

    def reset(self) -> None:
        """Reset scheduler state (clears pending and executed)."""
        self.pending.clear()
        self.executed.clear()

    def disable(self) -> None:
        """Disable the scheduler (stops checking triggers)."""
        self.enabled = False

    def enable(self) -> None:
        """Enable the scheduler (resumes checking triggers)."""
        self.enabled = True

    def get_pending_count(self) -> int:
        """Get count of pending interventions."""
        return len(self.pending)

    def get_executed_count(self) -> int:
        """Get count of executed interventions."""
        return len(self.executed)

    def get_execution_history(self) -> List[Tuple[int, Intervention]]:
        """
        Get the execution history.

        Returns:
            List of (step_idx, intervention) tuples in execution order
        """
        return self.executed.copy()

    def __repr__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return (
            f"InterventionScheduler({status}, "
            f"pending={len(self.pending)}, "
            f"executed={len(self.executed)})"
        )
