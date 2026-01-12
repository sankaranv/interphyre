"""
Event history and replay system for intervention tracking.

This module provides tools for recording trigger events during simulation,
enabling time-travel debugging and retrospective analysis.

## Usage

### Basic Recording

    from interphyre.interventions.history import EventHistoryRecorder

    recorder = EventHistoryRecorder()

    for step in range(max_steps):
        step_engine(engine)

        # Record events
        for trigger in triggers:
            if trigger.should_fire(step, engine):
                recorder.record_event(step, trigger, engine)

    # Access history
    history = recorder.get_history()
    print(f"Recorded {len(history.events)} events")

### Automatic Recording with SimulationIterator

    from interphyre.interventions import SimulationIterator
    from interphyre.interventions.history import record_simulation

    history = record_simulation(engine, triggers, max_steps=500)

    # Branch from specific event
    snapshot = history.get_snapshot(event_id=2)
    snapshot.restore(engine)

### Time-Travel Debugging

    # Get all contact events
    contact_events = history.filter_by_type("contact")

    # Jump to specific event
    snapshot = history.goto(event_id=5)

    # Replay from event
    for event in history.events[5:]:
        print(f"Step {event.step_index}: {event.trigger}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from interphyre.engine import Box2DEngine
    from interphyre.interventions.state import StateSnapshot
    from interphyre.interventions.triggers import Trigger


@dataclass
class SimulationEvent:
    """
    Record of a single event during simulation.

    Attributes:
        event_id: Unique identifier for this event
        step_index: Step when event occurred
        trigger: Trigger that fired
        snapshot: State snapshot at event time
        metadata: Additional event metadata
    """

    event_id: int
    step_index: int
    trigger: "Trigger"
    snapshot: "StateSnapshot"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"SimulationEvent(id={self.event_id}, "
            f"step={self.step_index}, trigger={self.trigger})"
        )


@dataclass
class EventHistory:
    """
    Container for recorded simulation events.

    Provides methods for filtering, searching, and replaying events.

    Attributes:
        events: List of recorded events
        metadata: History-level metadata
    """

    events: list[SimulationEvent] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        """Return number of recorded events."""
        return len(self.events)

    def __getitem__(self, index: int) -> SimulationEvent:
        """Get event by index."""
        return self.events[index]

    def get_snapshot(self, event_id: int) -> "StateSnapshot | None":
        """
        Get snapshot for specific event ID.

        Args:
            event_id: Event identifier

        Returns:
            StateSnapshot if found, None otherwise
        """
        for event in self.events:
            if event.event_id == event_id:
                return event.snapshot
        return None

    def goto(self, event_id: int) -> "StateSnapshot | None":
        """
        Jump to specific event (alias for get_snapshot).

        Args:
            event_id: Event identifier

        Returns:
            StateSnapshot if found, None otherwise
        """
        return self.get_snapshot(event_id)

    def filter_by_type(self, event_type: str) -> list[SimulationEvent]:
        """
        Filter events by type from metadata.

        Args:
            event_type: Type to filter by (e.g., "contact", "velocity_change")

        Returns:
            List of matching events

        Example:
            >>> contact_events = history.filter_by_type("contact")
            >>> for event in contact_events:
            ...     print(f"Contact at step {event.step_index}")
        """
        return [
            event
            for event in self.events
            if event.metadata.get("type") == event_type
        ]

    def filter_by_trigger(
        self, trigger_filter: Callable[["Trigger"], bool]
    ) -> list[SimulationEvent]:
        """
        Filter events by trigger condition.

        Args:
            trigger_filter: Function that takes Trigger and returns bool

        Returns:
            List of matching events

        Example:
            >>> # Find all contact triggers
            >>> def is_contact(t):
            ...     return "contact" in str(t).lower()
            >>> contact_events = history.filter_by_trigger(is_contact)
        """
        return [event for event in self.events if trigger_filter(event.trigger)]

    def filter_by_step_range(
        self, min_step: int, max_step: int
    ) -> list[SimulationEvent]:
        """
        Filter events by step index range.

        Args:
            min_step: Minimum step (inclusive)
            max_step: Maximum step (inclusive)

        Returns:
            List of events in range
        """
        return [
            event
            for event in self.events
            if min_step <= event.step_index <= max_step
        ]

    def get_by_object(self, obj_name: str) -> list[SimulationEvent]:
        """
        Get events involving specific object.

        Args:
            obj_name: Object name to search for

        Returns:
            List of events involving the object

        Example:
            >>> ball_events = history.get_by_object("green_ball")
        """
        return [
            event
            for event in self.events
            if obj_name in event.metadata.get("objects", [])
            or obj_name in str(event.trigger)
        ]

    def summary(self) -> dict[str, Any]:
        """
        Get summary statistics of event history.

        Returns:
            Dictionary with counts and info
        """
        if not self.events:
            return {"num_events": 0}

        event_types = {}
        for event in self.events:
            event_type = event.metadata.get("type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1

        return {
            "num_events": len(self.events),
            "first_step": self.events[0].step_index,
            "last_step": self.events[-1].step_index,
            "event_types": event_types,
        }


class EventHistoryRecorder:
    """
    Records events during simulation for later analysis.

    Automatically captures snapshots when triggers fire.

    Example:
        >>> recorder = EventHistoryRecorder()
        >>>
        >>> for step in range(max_steps):
        ...     step_engine(engine)
        ...     for trigger in triggers:
        ...         if trigger.should_fire(step, engine):
        ...             recorder.record_event(step, trigger, engine)
        >>>
        >>> history = recorder.get_history()
        >>> print(f"Recorded {len(history)} events")
    """

    def __init__(
        self,
        max_events: int | None = None,
        capture_snapshots: bool = True,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize event recorder.

        Args:
            max_events: Maximum events to record (None = unlimited)
            capture_snapshots: Whether to capture state snapshots
            metadata: Recorder-level metadata
        """
        self.max_events = max_events
        self.capture_snapshots = capture_snapshots
        self._events: list[SimulationEvent] = []
        self._next_event_id = 0
        self._metadata = metadata or {}

    def record_event(
        self,
        step_index: int,
        trigger: "Trigger",
        engine: "Box2DEngine",
        metadata: dict[str, Any] | None = None,
    ) -> SimulationEvent:
        """
        Record a trigger event.

        Args:
            step_index: Current step index
            trigger: Trigger that fired
            engine: Engine instance
            metadata: Event-specific metadata

        Returns:
            The created SimulationEvent
        """
        from interphyre.interventions.state import StateSnapshot

        # Check max events limit
        if self.max_events is not None and len(self._events) >= self.max_events:
            return self._events[-1]  # Return last event if at limit

        # Capture snapshot if enabled
        snapshot = None
        if self.capture_snapshots:
            snapshot = StateSnapshot.capture(
                engine,
                metadata={
                    "event_id": self._next_event_id,
                    "step_index": step_index,
                    "trigger": str(trigger),
                },
            )

        # Create event
        event = SimulationEvent(
            event_id=self._next_event_id,
            step_index=step_index,
            trigger=trigger,
            snapshot=snapshot,
            metadata=metadata or {},
        )

        self._events.append(event)
        self._next_event_id += 1

        return event

    def get_history(self) -> EventHistory:
        """
        Get the recorded event history.

        Returns:
            EventHistory containing all recorded events
        """
        return EventHistory(events=self._events.copy(), metadata=self._metadata.copy())

    def clear(self) -> None:
        """Clear all recorded events."""
        self._events.clear()
        self._next_event_id = 0


def record_simulation(
    engine: "Box2DEngine",
    triggers: list["Trigger"],
    max_steps: int = 500,
    max_events: int | None = None,
) -> EventHistory:
    """
    Run simulation and record all trigger events.

    This is a convenience function that combines simulation execution
    with automatic event recording.

    Args:
        engine: Box2DEngine instance
        triggers: List of triggers to monitor
        max_steps: Maximum simulation steps
        max_events: Maximum events to record (None = unlimited)

    Returns:
        EventHistory with recorded events

    Example:
        >>> from interphyre.interventions import on_contact, on_success
        >>>
        >>> triggers = [
        ...     on_contact("ball", "target"),
        ...     on_success()
        ... ]
        >>>
        >>> history = record_simulation(engine, triggers, max_steps=240)
        >>> print(f"Recorded {len(history)} events")
        >>>
        >>> # Branch from first contact
        >>> contact_events = history.filter_by_type("contact")
        >>> if contact_events:
        ...     snapshot = contact_events[0].snapshot
        ...     snapshot.restore(engine)
    """
    from interphyre.interventions.agent_api import step_engine

    recorder = EventHistoryRecorder(max_events=max_events)

    for step_index in range(max_steps):
        step_engine(engine)

        for trigger in triggers:
            if trigger.should_fire(step_index + 1, engine):
                # Determine event type from trigger
                trigger_str = str(trigger).lower()
                if "contact" in trigger_str:
                    event_type = "contact"
                elif "velocity" in trigger_str:
                    event_type = "velocity"
                elif "position" in trigger_str:
                    event_type = "position"
                elif "success" in trigger_str:
                    event_type = "success"
                else:
                    event_type = "custom"

                recorder.record_event(
                    step_index + 1,
                    trigger,
                    engine,
                    metadata={"type": event_type},
                )

    return recorder.get_history()


def branch_from_event(
    history: EventHistory,
    event_id: int,
    intervention: "Callable | None" = None,
) -> "StateSnapshot | None":
    """
    Branch from a specific event in history.

    Args:
        history: EventHistory to branch from
        event_id: ID of event to branch from
        intervention: Optional intervention to apply after restoring

    Returns:
        StateSnapshot at event, or None if not found

    Example:
        >>> # Branch from event 3 with intervention
        >>> snapshot = branch_from_event(history, event_id=3, intervention=my_intervention)
        >>> if snapshot:
        ...     snapshot.restore(engine)
        ...     # Continue simulation from this point
    """
    snapshot = history.get_snapshot(event_id)

    if snapshot and intervention:
        from interphyre.interventions.core import CallableIntervention

        # Get engine from snapshot
        engine = snapshot._engine

        # Restore snapshot
        snapshot.restore(engine)

        # Apply intervention
        if callable(intervention):
            if not isinstance(intervention, CallableIntervention):
                intervention = CallableIntervention(intervention)
            intervention.apply(engine)

    return snapshot


def replay_to_event(
    engine: "Box2DEngine",
    history: EventHistory,
    target_event_id: int,
    apply_interventions: bool = False,
) -> bool:
    """
    Replay simulation to specific event.

    Args:
        engine: Box2DEngine instance (will be reset)
        history: EventHistory to replay
        target_event_id: Event to replay to
        apply_interventions: Whether to apply recorded interventions

    Returns:
        True if successfully replayed, False otherwise

    Example:
        >>> # Replay to event 5
        >>> success = replay_to_event(engine, history, target_event_id=5)
        >>> if success:
        ...     # Engine is now at state of event 5
        ...     pass
    """
    snapshot = history.get_snapshot(target_event_id)

    if snapshot is None:
        return False

    # Restore to target snapshot
    snapshot.restore(engine)
    return True
