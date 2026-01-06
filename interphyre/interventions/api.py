"""
High-level API for intervention management.

This module provides Pythonic context managers and utilities for working with
interventions in a clean, intuitive way. Includes automatic rollback on exceptions,
helper methods for common operations, and fluent interfaces.
"""

from contextlib import contextmanager
from typing import TYPE_CHECKING, Optional, Tuple, Any
from dataclasses import dataclass, field

from interphyre.interventions.state import StateSnapshot
from interphyre.config import PRECISION

if TYPE_CHECKING:
    from interphyre.engine import Box2DEngine


@dataclass
class InterventionContext:
    """
    Context manager for applying interventions with automatic rollback.

    Features:
    - Automatic snapshot capture on entry
    - Rollback to snapshot on exception
    - Helper methods for common interventions
    - Modification tracking for reproducibility

    Example:
        with InterventionContext(engine) as ctx:
            ctx.set_position("green_ball", x=2.0, y=3.0)
            ctx.set_velocity("red_ball", vx=0.0, vy=-1.0)
            # If exception occurs, automatically rolls back
    """

    engine: "Box2DEngine"
    auto_rollback: bool = True
    snapshot: Optional[StateSnapshot] = field(default=None, init=False)
    modifications: list[dict[str, Any]] = field(default_factory=list, init=False)

    def __enter__(self) -> "InterventionContext":
        """Capture snapshot on context entry."""
        self.snapshot = StateSnapshot.capture(self.engine)
        self.modifications = []
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Rollback on exception if auto_rollback is enabled."""
        if exc_type is not None and self.auto_rollback and self.snapshot is not None:
            self.snapshot.restore(self.engine)
        return False  # Don't suppress exceptions

    def set_position(self, obj_name: str, x: Optional[float] = None, y: Optional[float] = None) -> "InterventionContext":
        """
        Set object position.

        Args:
            obj_name: Name of the object to modify
            x: New x position (None to keep current)
            y: New y position (None to keep current)

        Returns:
            Self for method chaining
        """
        body = self.engine.bodies.get(obj_name)
        if body is None:
            raise ValueError(f"Object '{obj_name}' not found in engine")

        current_pos = body.position
        new_x = round(x, PRECISION) if x is not None else current_pos.x
        new_y = round(y, PRECISION) if y is not None else current_pos.y

        from Box2D import b2Vec2
        body.transform = (b2Vec2(new_x, new_y), body.angle)

        step_count = int(
            round(self.engine.contact_listener.current_time / self.engine.config.time_step)
        )
        self.modifications.append({
            "type": "set_position",
            "object": obj_name,
            "x": new_x,
            "y": new_y,
            "step": step_count
        })

        return self

    def set_velocity(self, obj_name: str, vx: Optional[float] = None, vy: Optional[float] = None) -> "InterventionContext":
        """
        Set object linear velocity.

        Args:
            obj_name: Name of the object to modify
            vx: New x velocity (None to keep current)
            vy: New y velocity (None to keep current)

        Returns:
            Self for method chaining
        """
        body = self.engine.bodies.get(obj_name)
        if body is None:
            raise ValueError(f"Object '{obj_name}' not found in engine")

        current_vel = body.linearVelocity
        new_vx = round(vx, PRECISION) if vx is not None else current_vel.x
        new_vy = round(vy, PRECISION) if vy is not None else current_vel.y

        from Box2D import b2Vec2
        body.linearVelocity = b2Vec2(new_vx, new_vy)

        step_count = int(
            round(self.engine.contact_listener.current_time / self.engine.config.time_step)
        )
        self.modifications.append({
            "type": "set_velocity",
            "object": obj_name,
            "vx": new_vx,
            "vy": new_vy,
            "step": step_count
        })

        return self

    def multiply_velocity(self, obj_name: str, factor: float) -> "InterventionContext":
        """
        Multiply object velocity by a scalar factor.

        Args:
            obj_name: Name of the object to modify
            factor: Multiplicative factor

        Returns:
            Self for method chaining
        """
        body = self.engine.bodies.get(obj_name)
        if body is None:
            raise ValueError(f"Object '{obj_name}' not found in engine")

        current_vel = body.linearVelocity
        new_vx = round(current_vel.x * factor, PRECISION)
        new_vy = round(current_vel.y * factor, PRECISION)

        from Box2D import b2Vec2
        body.linearVelocity = b2Vec2(new_vx, new_vy)

        step_count = int(
            round(self.engine.contact_listener.current_time / self.engine.config.time_step)
        )
        self.modifications.append({
            "type": "multiply_velocity",
            "object": obj_name,
            "factor": factor,
            "step": step_count
        })

        return self

    def set_angle(self, obj_name: str, angle: float) -> "InterventionContext":
        """
        Set object rotation angle.

        Args:
            obj_name: Name of the object to modify
            angle: New angle in radians

        Returns:
            Self for method chaining
        """
        body = self.engine.bodies.get(obj_name)
        if body is None:
            raise ValueError(f"Object '{obj_name}' not found in engine")

        angle = round(angle, PRECISION)
        from Box2D import b2Vec2
        body.transform = (b2Vec2(body.position.x, body.position.y), angle)

        step_count = int(
            round(self.engine.contact_listener.current_time / self.engine.config.time_step)
        )
        self.modifications.append({
            "type": "set_angle",
            "object": obj_name,
            "angle": angle,
            "step": step_count
        })

        return self

    def set_angular_velocity(self, obj_name: str, omega: float) -> "InterventionContext":
        """
        Set object angular velocity.

        Args:
            obj_name: Name of the object to modify
            omega: New angular velocity in radians/second

        Returns:
            Self for method chaining
        """
        body = self.engine.bodies.get(obj_name)
        if body is None:
            raise ValueError(f"Object '{obj_name}' not found in engine")

        omega = round(omega, PRECISION)
        body.angularVelocity = omega

        step_count = int(
            round(self.engine.contact_listener.current_time / self.engine.config.time_step)
        )
        self.modifications.append({
            "type": "set_angular_velocity",
            "object": obj_name,
            "omega": omega,
            "step": step_count
        })

        return self

    def set_gravity(self, gravity: Tuple[float, float]) -> "InterventionContext":
        """
        Set world gravity.

        Args:
            gravity: Tuple of (gx, gy) gravity components

        Returns:
            Self for method chaining
        """
        gx, gy = gravity
        gx = round(gx, PRECISION)
        gy = round(gy, PRECISION)

        from Box2D import b2Vec2
        self.engine.world.gravity = b2Vec2(gx, gy)

        step_count = int(
            round(self.engine.contact_listener.current_time / self.engine.config.time_step)
        )
        self.modifications.append({
            "type": "set_gravity",
            "gravity": (gx, gy),
            "step": step_count
        })

        return self

    def apply_impulse(self, obj_name: str, impulse: Tuple[float, float], point: Optional[Tuple[float, float]] = None) -> "InterventionContext":
        """
        Apply an impulse to an object.

        Args:
            obj_name: Name of the object to modify
            impulse: Tuple of (ix, iy) impulse components
            point: Point to apply impulse (world coordinates). If None, uses center of mass.

        Returns:
            Self for method chaining
        """
        body = self.engine.bodies.get(obj_name)
        if body is None:
            raise ValueError(f"Object '{obj_name}' not found in engine")

        ix, iy = impulse
        ix = round(ix, PRECISION)
        iy = round(iy, PRECISION)

        from Box2D import b2Vec2
        if point is None:
            point_vec = body.worldCenter
            point_tuple = (point_vec.x, point_vec.y)
        else:
            px, py = point
            point_vec = b2Vec2(round(px, PRECISION), round(py, PRECISION))
            point_tuple = (point_vec.x, point_vec.y)

        body.ApplyLinearImpulse(b2Vec2(ix, iy), point_vec, True)

        step_count = int(
            round(self.engine.contact_listener.current_time / self.engine.config.time_step)
        )
        self.modifications.append({
            "type": "apply_impulse",
            "object": obj_name,
            "impulse": (ix, iy),
            "point": point_tuple,
            "step": step_count
        })

        return self

    def freeze(self, obj_name: str) -> "InterventionContext":
        """
        Freeze an object by setting its velocity to zero.

        Args:
            obj_name: Name of the object to modify

        Returns:
            Self for method chaining
        """
        return self.set_velocity(obj_name, vx=0.0, vy=0.0).set_angular_velocity(obj_name, omega=0.0)

    def get_modifications(self) -> list[dict[str, Any]]:
        """
        Get list of all modifications applied in this context.

        Returns:
            List of modification dictionaries with type, object, parameters, and step
        """
        return self.modifications.copy()


@contextmanager
def with_intervention(engine: "Box2DEngine", auto_rollback: bool = True):
    """
    Context manager for applying interventions with automatic rollback.

    Args:
        engine: The Box2D engine to modify
        auto_rollback: If True, automatically rollback on exception

    Yields:
        InterventionContext for applying modifications

    Example:
        with with_intervention(engine) as ctx:
            ctx.set_position("green_ball", x=2.0, y=3.0)
            ctx.set_velocity("red_ball", vx=0.0, vy=-1.0)
    """
    ctx = InterventionContext(engine, auto_rollback=auto_rollback)
    try:
        yield ctx.__enter__()
    except Exception as e:
        ctx.__exit__(type(e), e, e.__traceback__)
        raise
    else:
        ctx.__exit__(None, None, None)


@contextmanager
def counterfactual_intervention(engine: "Box2DEngine"):
    """
    Context manager specifically for counterfactual analysis.

    This is an alias for with_intervention with auto_rollback=False,
    making it clear that modifications are permanent (for counterfactual branch).

    Args:
        engine: The Box2D engine to modify

    Yields:
        InterventionContext for applying modifications

    Example:
        snapshot = StateSnapshot.capture(engine)

        # Factual branch - continue without intervention
        factual_result = run_simulation(engine, steps=50)

        # Counterfactual branch - apply intervention
        snapshot.restore(engine)
        with counterfactual_intervention(engine) as cf:
            cf.set_velocity("red_ball", vx=2.0)
        cf_result = run_simulation(engine, steps=50)
    """
    with with_intervention(engine, auto_rollback=False) as ctx:
        yield ctx
