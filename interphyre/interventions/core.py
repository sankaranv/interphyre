"""
Core base classes for the interventions system.

This module defines the foundational abstract base classes and protocols
that other intervention components build upon.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from interphyre.engine import Box2DEngine


class Intervention(ABC):
    """
    Abstract base class for all interventions.

    An intervention represents a modification to the simulation state
    that can be applied at a specific point in time.
    """

    @abstractmethod
    def apply(self, engine: "Box2DEngine") -> None:
        """
        Apply this intervention to the simulation engine.

        Args:
            engine: The Box2D engine to modify
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class CallableIntervention(Intervention):
    """
    Intervention that wraps a callable function.

    This allows using lambda functions or regular functions as interventions.
    """

    def __init__(self, func: Callable[["Box2DEngine"], None], name: str | None = None):
        """
        Initialize a callable intervention.

        Args:
            func: Callable that takes Box2DEngine as argument
            name: Optional name for logging/debugging
        """
        self.func = func
        self.name = name or f"callable_{id(func)}"

    def apply(self, engine: "Box2DEngine") -> None:
        """Apply the wrapped callable to the engine."""
        self.func(engine)

    def __repr__(self) -> str:
        return f"CallableIntervention(name='{self.name}')"
