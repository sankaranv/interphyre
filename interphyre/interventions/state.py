"""
State snapshot and restoration functionality.

This module provides the StateSnapshot class for capturing and restoring
complete simulation state, enabling deterministic replay and branching.
"""

import hashlib
import pickle
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, Set, TYPE_CHECKING

from interphyre.interventions.serialization import (
    serialize_box2d_world,
    deserialize_box2d_world,
)

if TYPE_CHECKING:
    from interphyre.engine import Box2DEngine


@dataclass(frozen=True)
class StateSnapshot:
    """
    Immutable snapshot of complete simulation state.

    This captures everything needed to restore the simulation to an exact
    state, including Box2D physics state, contact tracking, and metadata.

    Attributes:
        step_count: Simulation step count when snapshot was taken
        current_time: Simulation time in seconds
        objects: PhyreObject state (position, velocity, etc.)
        box2d_state: Serialized Box2D world state
        contacts: Set of active contact pairs
        contact_start_times: Start time of each contact
        level_hash: Hash of level configuration for validation
        metadata: Optional user-provided metadata
    """

    step_count: int
    current_time: float
    objects: Dict[str, Dict[str, Any]]
    box2d_state: bytes
    contacts: FrozenSet[FrozenSet[str]]
    contact_start_times: Dict[str, float]
    level_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def capture(
        cls, engine: "Box2DEngine", metadata: Dict[str, Any] | None = None
    ) -> "StateSnapshot":
        """
        Capture complete engine state as an immutable snapshot.

        Args:
            engine: The Box2DEngine to snapshot
            metadata: Optional metadata to attach to snapshot

        Returns:
            Immutable StateSnapshot containing complete state
        """
        # Capture object states from Box2D bodies
        objects = {}
        if engine.level is None:
            raise ValueError(
                "Level is not set. Please call reset() with a valid level before capturing state."
            )
        if engine.level.objects is None:
            raise ValueError(
                "Level objects are not set. Please call reset() with a valid level before capturing state."
            )
        for name in engine.level.objects.keys():
            if name in engine.bodies:
                body = engine.bodies[name]
                objects[name] = {
                    "position": (body.position.x, body.position.y),
                    "velocity": (body.linearVelocity.x, body.linearVelocity.y),
                    "angle": body.angle,
                    "angular_velocity": body.angularVelocity,
                    "type": type(engine.level.objects[name]).__name__,
                    "dynamic": body.type == 2,  # b2_dynamicBody
                }
            else:
                # Object not yet placed (e.g., action objects before placement)
                obj = engine.level.objects[name]
                objects[name] = {
                    "position": (obj.x, obj.y),
                    "velocity": (0.0, 0.0),
                    "angle": obj.angle,
                    "angular_velocity": 0.0,
                    "type": type(obj).__name__,
                    "dynamic": obj.dynamic,
                }

        # Serialize Box2D world state
        box2d_state = serialize_box2d_world(engine.world, engine.bodies)

        # Capture contact tracking state
        contacts = frozenset(engine.contact_listener.contacts)

        # Convert contact_start_time dict to serializable format
        # contact_start_time has frozenset keys, convert to string keys
        contact_start_times = {
            f"{sorted(pair)[0]}_{sorted(pair)[1]}": time
            for pair, time in engine.contact_listener.contact_start_time.items()
        }

        # Compute level hash for validation
        level_hash = cls._hash_level(engine.level)

        # Calculate step count from current time
        step_count = int(
            round(engine.contact_listener.current_time / engine.config.time_step)
        )

        return cls(
            step_count=step_count,
            current_time=engine.contact_listener.current_time,
            objects=objects,
            box2d_state=box2d_state,
            contacts=contacts,
            contact_start_times=contact_start_times,
            level_hash=level_hash,
            metadata=metadata or {},
        )

    def restore(self, engine: "Box2DEngine") -> None:
        """
        Restore engine to this snapshot state.

        This performs a complete state restoration, ensuring the engine
        returns to the exact state when the snapshot was captured.

        Args:
            engine: The Box2DEngine to restore

        Raises:
            ValueError: If snapshot level doesn't match engine level
        """
        # Validate level matches
        if self.level_hash != self._hash_level(engine.level):
            raise ValueError(
                "Cannot restore snapshot to different level. "
                "Snapshot level hash does not match current engine level."
            )

        # Restore Box2D world state
        deserialize_box2d_world(engine.world, engine.bodies, self.box2d_state)

        # Clear all forces to ensure clean state
        engine.world.ClearForces()

        # Restore contact listener state
        engine.contact_listener.contacts = set(self.contacts)

        # Restore contact start times (convert string keys back to frozensets)
        engine.contact_listener.contact_start_time = {}
        for key, time in self.contact_start_times.items():
            obj1, obj2 = key.split("_", 1)
            pair = frozenset([obj1, obj2])
            engine.contact_listener.contact_start_time[pair] = time

        engine.contact_listener.current_time = self.current_time

    @staticmethod
    def _hash_level(level) -> str:
        """
        Compute deterministic hash of level configuration.

        Args:
            level: The Level object to hash

        Returns:
            Hash string identifying the level
        """
        # Create hashable representation of level
        obj_data = tuple(
            sorted(
                [
                    (
                        name,
                        type(obj).__name__,
                        round(obj.x, 8),
                        round(obj.y, 8),
                        round(obj.angle, 8),
                    )
                    for name, obj in level.objects.items()
                ]
            )
        )

        hash_input = str(
            (
                level.name,
                obj_data,
                tuple(sorted(level.action_objects)),
            )
        )

        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def to_bytes(self) -> bytes:
        """
        Serialize snapshot to bytes for storage.

        Returns:
            Pickled bytes containing complete snapshot
        """
        return pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def from_bytes(cls, data: bytes) -> "StateSnapshot":
        """
        Deserialize snapshot from bytes.

        Args:
            data: Pickled bytes containing snapshot

        Returns:
            StateSnapshot instance
        """
        return pickle.loads(data)

    def __eq__(self, other: Any) -> bool:
        """
        Check equality with another snapshot.

        Two snapshots are equal if they represent the same simulation state,
        excluding metadata.

        Args:
            other: Object to compare with

        Returns:
            True if snapshots represent same state
        """
        if not isinstance(other, StateSnapshot):
            return False

        return (
            self.step_count == other.step_count
            and abs(self.current_time - other.current_time) < 1e-9
            and self.objects == other.objects
            and self.box2d_state == other.box2d_state
            and self.contacts == other.contacts
            and self.contact_start_times == other.contact_start_times
            and self.level_hash == other.level_hash
        )

    def __repr__(self) -> str:
        return (
            f"StateSnapshot(step={self.step_count}, "
            f"time={self.current_time:.3f}s, "
            f"objects={len(self.objects)}, "
            f"contacts={len(self.contacts)})"
        )
