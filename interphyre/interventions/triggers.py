"""
Trigger system for intervention scheduling.

This module defines triggers that determine when interventions should fire
during simulation. Supports time-based, event-based, and condition-based triggers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, FrozenSet, TYPE_CHECKING

if TYPE_CHECKING:
    from interphyre.engine import Box2DEngine


@dataclass
class Trigger(ABC):
    """
    Abstract base class for all intervention triggers.

    A trigger determines when an intervention should fire during simulation.
    Triggers are evaluated each simulation step.

    Attributes:
        priority: Lower values execute first (default: 0)
    """

    priority: int = 0

    @abstractmethod
    def should_fire(self, step_idx: int, engine: "Box2DEngine") -> bool:
        """
        Check if this trigger should fire at the current step.

        Args:
            step_idx: Current simulation step index
            engine: The Box2DEngine being simulated

        Returns:
            True if trigger should fire, False otherwise
        """
        pass

    def reset(self) -> None:
        """
        Reset trigger state (for once-only triggers that need to be reused).

        Override in subclasses if needed.
        """
        pass


@dataclass
class TimeBasedTrigger(Trigger):
    """
    Trigger that fires at a specific simulation step.

    This is the simplest trigger type - fires once at a predetermined step.

    Attributes:
        target_step: The step index at which to fire
        priority: Execution priority (default: 0)
    """

    target_step: int = 0
    priority: int = 0

    def should_fire(self, step_idx: int, engine: "Box2DEngine") -> bool:
        """Fire when current step matches target step."""
        return step_idx == self.target_step

    def __repr__(self) -> str:
        return f"TimeBasedTrigger(step={self.target_step}, priority={self.priority})"


@dataclass
class EventBasedTrigger(Trigger):
    """
    Trigger that fires when a simulation event occurs.

    Supports contact events, success conditions, and other state-based events.

    Attributes:
        event_type: Type of event ("contact", "success", etc.)
        object_names: Names of objects involved in the event
        once_only: If True, fire only once (default: True)
        priority: Execution priority (default: 0)
    """

    event_type: str = "contact"
    object_names: tuple[str, ...] = field(default_factory=tuple)
    once_only: bool = True
    priority: int = 0
    _fired: bool = field(default=False, init=False, repr=False)

    def should_fire(self, step_idx: int, engine: "Box2DEngine") -> bool:
        """Fire when specified event occurs."""
        if self.once_only and self._fired:
            return False

        fired = self._check_event(engine)

        if fired and self.once_only:
            self._fired = True

        return fired

    def _check_event(self, engine: "Box2DEngine") -> bool:
        """Check if the event has occurred."""
        if self.event_type == "contact":
            if len(self.object_names) == 2:
                # Specific contact pair
                contact_pair = frozenset(self.object_names)
                return contact_pair in engine.contact_listener.contacts
            elif len(self.object_names) == 1:
                # Any contact involving this object
                obj_name = self.object_names[0]
                for contact in engine.contact_listener.contacts:
                    if obj_name in contact:
                        return True
                return False
            else:
                raise ValueError("EventBasedTrigger requires 1 or 2 object names")

        elif self.event_type == "success":
            # Success condition met
            if engine.level and engine.level.success_condition:
                return engine.level.success_condition(engine)
            return False

        else:
            raise ValueError(f"Unknown event type: {self.event_type}")

    def reset(self) -> None:
        """Reset fired state for reuse."""
        self._fired = False

    def __repr__(self) -> str:
        once_str = "once" if self.once_only else "repeat"
        return (
            f"EventBasedTrigger(type={self.event_type}, "
            f"objects={self.object_names}, {once_str}, priority={self.priority})"
        )


@dataclass
class ConditionBasedTrigger(Trigger):
    """
    Trigger that fires when a custom condition is met.

    This is the most flexible trigger type - accepts any callable that
    returns a boolean based on engine state.

    Attributes:
        condition: Callable that takes engine and returns bool
        once_only: If True, fire only once (default: True)
        priority: Execution priority (default: 0)
    """

    condition: Callable[["Box2DEngine"], bool] = field(default=lambda e: False)
    once_only: bool = True
    priority: int = 0
    _fired: bool = field(default=False, init=False, repr=False)

    def should_fire(self, step_idx: int, engine: "Box2DEngine") -> bool:
        """Fire when custom condition returns True."""
        if self.once_only and self._fired:
            return False

        try:
            result = self.condition(engine)
        except Exception as e:
            # Log warning but don't crash simulation
            import logging

            logging.warning(f"Condition evaluation failed: {e}")
            return False

        if result and self.once_only:
            self._fired = True

        return result

    def reset(self) -> None:
        """Reset fired state for reuse."""
        self._fired = False

    def __repr__(self) -> str:
        once_str = "once" if self.once_only else "repeat"
        condition_name = getattr(self.condition, "__name__", "custom")
        return f"ConditionBasedTrigger(condition={condition_name}, {once_str}, priority={self.priority})"


# Convenience functions for creating triggers


def at_step(step: int, priority: int = 0) -> TimeBasedTrigger:
    """
    Create a time-based trigger that fires at a specific step.

    Args:
        step: Step index at which to fire
        priority: Execution priority (default: 0)

    Returns:
        TimeBasedTrigger configured for the specified step
    """
    return TimeBasedTrigger(target_step=step, priority=priority)


def on_contact(obj1: str, obj2: str, once: bool = True, priority: int = 0) -> EventBasedTrigger:
    """
    Create an event-based trigger that fires when two objects contact.

    Args:
        obj1: First object name
        obj2: Second object name
        once: If True, fire only once (default: True)
        priority: Execution priority (default: 0)

    Returns:
        EventBasedTrigger configured for contact between obj1 and obj2
    """
    return EventBasedTrigger(
        event_type="contact",
        object_names=(obj1, obj2),
        once_only=once,
        priority=priority,
    )


def on_contact_with(obj: str, once: bool = True, priority: int = 0) -> EventBasedTrigger:
    """
    Create an event-based trigger that fires when an object contacts anything.

    Args:
        obj: Object name
        once: If True, fire only once (default: True)
        priority: Execution priority (default: 0)

    Returns:
        EventBasedTrigger configured for any contact involving obj
    """
    return EventBasedTrigger(
        event_type="contact",
        object_names=(obj,),
        once_only=once,
        priority=priority,
    )


def on_success(once: bool = True, priority: int = 0) -> EventBasedTrigger:
    """
    Create an event-based trigger that fires when success condition is met.

    Args:
        once: If True, fire only once (default: True)
        priority: Execution priority (default: 0)

    Returns:
        EventBasedTrigger configured for success condition
    """
    return EventBasedTrigger(
        event_type="success",
        object_names=(),
        once_only=once,
        priority=priority,
    )


def when(
    condition: Callable[["Box2DEngine"], bool],
    once: bool = True,
    priority: int = 0,
) -> ConditionBasedTrigger:
    """
    Create a condition-based trigger that fires when a custom condition is met.

    Args:
        condition: Callable that takes Box2DEngine and returns bool
        once: If True, fire only once (default: True)
        priority: Execution priority (default: 0)

    Returns:
        ConditionBasedTrigger configured with the custom condition

    Example:
        >>> trigger = when(lambda e: e.bodies["ball"].position.y < -2.0)
    """
    return ConditionBasedTrigger(
        condition=condition,
        once_only=once,
        priority=priority,
    )
