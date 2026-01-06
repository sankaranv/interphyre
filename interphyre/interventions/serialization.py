"""
Box2D state serialization utilities.

This module provides functions for serializing and deserializing Box2D world state,
including bodies, fixtures, contacts, and solver state. This enables deterministic
state capture and restoration for intervention experiments.
"""

import pickle
from typing import Any, Dict, List, Tuple
from Box2D import b2World, b2Body, b2Fixture


def serialize_body(body: b2Body) -> Dict[str, Any]:
    """
    Serialize a single Box2D body to a dictionary.

    Args:
        body: The b2Body to serialize

    Returns:
        Dictionary containing all body state
    """
    # Serialize fixtures
    fixtures = []
    for fixture in body.fixtures:
        fixture_data = {
            "density": fixture.density,
            "friction": fixture.friction,
            "restitution": fixture.restitution,
            "sensor": fixture.sensor,
            "filter_category_bits": fixture.filterData.categoryBits,
            "filter_mask_bits": fixture.filterData.maskBits,
            "filter_group_index": fixture.filterData.groupIndex,
            # Shape is recreated from PhyreObject, not serialized here
        }
        fixtures.append(fixture_data)

    return {
        "user_data": body.userData,
        "position": (body.position.x, body.position.y),
        "angle": body.angle,
        "linear_velocity": (body.linearVelocity.x, body.linearVelocity.y),
        "angular_velocity": body.angularVelocity,
        "linear_damping": body.linearDamping,
        "angular_damping": body.angularDamping,
        "gravity_scale": body.gravityScale,
        "bullet": body.bullet,
        "awake": body.awake,
        "active": body.active,
        "fixed_rotation": body.fixedRotation,
        "type": body.type,  # 0=static, 1=kinematic, 2=dynamic
        "fixtures": fixtures,
    }


def restore_body_state(body: b2Body, body_data: Dict[str, Any]) -> None:
    """
    Restore a Box2D body's state from serialized data.

    This updates an existing body rather than creating a new one, since
    the body must already exist with the correct fixtures/shapes from
    the level definition.

    Args:
        body: The existing b2Body to update
        body_data: Dictionary containing serialized body state
    """
    # Wake the body first to ensure it can be modified
    was_awake = body_data["awake"]
    if not was_awake:
        # Temporarily wake to allow setting position/velocity
        body.awake = True

    # Restore transform (position and angle)
    # Use SetTransform to properly update Box2D internal state
    from Box2D import b2Vec2
    body.transform = (b2Vec2(*body_data["position"]), body_data["angle"])

    # Restore velocities
    body.linearVelocity = b2Vec2(*body_data["linear_velocity"])
    body.angularVelocity = body_data["angular_velocity"]
    body.linearDamping = body_data["linear_damping"]
    body.angularDamping = body_data["angular_damping"]
    body.gravityScale = body_data["gravity_scale"]
    body.bullet = body_data["bullet"]
    body.active = body_data["active"]
    body.fixedRotation = body_data["fixed_rotation"]
    # Note: body.type cannot be changed after creation

    # Restore fixture properties
    for fixture, fixture_data in zip(body.fixtures, body_data["fixtures"]):
        fixture.density = fixture_data["density"]
        fixture.friction = fixture_data["friction"]
        fixture.restitution = fixture_data["restitution"]
        fixture.sensor = fixture_data["sensor"]
        # Filter data
        filter_data = fixture.filterData
        filter_data.categoryBits = fixture_data["filter_category_bits"]
        filter_data.maskBits = fixture_data["filter_mask_bits"]
        filter_data.groupIndex = fixture_data["filter_group_index"]
        fixture.filterData = filter_data

    # Reset mass data after modifying fixtures
    body.ResetMassData()

    # Restore awake state
    body.awake = was_awake


def serialize_world_properties(world: b2World) -> Dict[str, Any]:
    """
    Serialize Box2D world-level properties.

    Args:
        world: The b2World to serialize

    Returns:
        Dictionary containing world properties
    """
    return {
        "gravity": (world.gravity.x, world.gravity.y),
        "warm_starting": world.warmStarting,
        "substepping": world.subStepping,
        "continuous_physics": world.continuousPhysics,
        "body_count": world.bodyCount,
        "contact_count": world.contactCount,
    }


def restore_world_properties(world: b2World, world_data: Dict[str, Any]) -> None:
    """
    Restore Box2D world-level properties.

    Args:
        world: The b2World to update
        world_data: Dictionary containing serialized world properties
    """
    world.gravity = tuple(world_data["gravity"])
    world.warmStarting = world_data["warm_starting"]
    world.subStepping = world_data["substepping"]
    world.continuousPhysics = world_data["continuous_physics"]


def serialize_box2d_world(world: b2World, body_names: Dict[str, b2Body]) -> bytes:
    """
    Serialize complete Box2D world state to bytes.

    Args:
        world: The b2World to serialize
        body_names: Mapping from object names to b2Body objects

    Returns:
        Pickled bytes containing complete world state
    """
    state = {
        "world_properties": serialize_world_properties(world),
        "bodies": {name: serialize_body(body) for name, body in sorted(body_names.items())},
    }
    return pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)


def deserialize_box2d_world(
    world: b2World, body_names: Dict[str, b2Body], data: bytes
) -> None:
    """
    Restore Box2D world state from serialized bytes.

    This updates the existing world and bodies rather than creating new ones,
    since the world structure (bodies, fixtures, shapes) must match the level.

    Args:
        world: The existing b2World to update
        body_names: Mapping from object names to existing b2Body objects
        data: Pickled bytes containing serialized world state
    """
    state = pickle.loads(data)

    # Restore world properties
    restore_world_properties(world, state["world_properties"])

    # Restore body states
    for name, body_data in state["bodies"].items():
        if name in body_names:
            restore_body_state(body_names[name], body_data)

    # Clear forces after restoration
    world.ClearForces()
