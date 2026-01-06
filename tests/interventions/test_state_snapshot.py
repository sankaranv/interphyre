"""
Unit tests for StateSnapshot class.

Tests cover:
- State capture and restoration
- Determinism verification
- Snapshot immutability
- All object types (Ball, Bar, Basket)
- Contact state preservation
- Level validation
"""

import pytest
import numpy as np
from interphyre.environment import PhyreEnv
from interphyre.config import SimulationConfig
from interphyre.interventions import StateSnapshot
from interphyre.levels import load_level


class TestStateSnapshotBasics:
    """Test basic snapshot capture and restore functionality."""

    def test_capture_creates_immutable_snapshot(self):
        """Test that capture creates an immutable frozen dataclass."""
        level = load_level("two_body_problem", seed=42)
        config = SimulationConfig(enable_interventions=True)
        env = PhyreEnv(level, config=config)
        obs, info = env.reset()

        # Place action object
        action = [(0, 3, 0.8)]
        env.step(action)

        # Capture snapshot
        snapshot = StateSnapshot.capture(env.engine)

        # Verify it's a StateSnapshot instance
        assert isinstance(snapshot, StateSnapshot)

        # Verify immutability - should not be able to modify
        with pytest.raises(Exception):  # FrozenInstanceError or similar
            snapshot.step_count = 999

    def test_snapshot_contains_required_fields(self):
        """Test that snapshot contains all required state fields."""
        level = load_level("two_body_problem", seed=42)
        config = SimulationConfig(enable_interventions=True)
        env = PhyreEnv(level, config=config)
        env.reset()
        env.step([(0, 3, 0.8)])

        snapshot = StateSnapshot.capture(env.engine)

        # Check all required fields exist
        assert hasattr(snapshot, "step_count")
        assert hasattr(snapshot, "current_time")
        assert hasattr(snapshot, "objects")
        assert hasattr(snapshot, "box2d_state")
        assert hasattr(snapshot, "contacts")
        assert hasattr(snapshot, "contact_start_times")
        assert hasattr(snapshot, "level_hash")
        assert hasattr(snapshot, "metadata")

        # Check field types
        assert isinstance(snapshot.step_count, int)
        assert isinstance(snapshot.current_time, float)
        assert isinstance(snapshot.objects, dict)
        assert isinstance(snapshot.box2d_state, bytes)
        assert isinstance(snapshot.level_hash, str)
        assert isinstance(snapshot.metadata, dict)

    def test_restore_same_level_succeeds(self):
        """Test that restore works on the same level."""
        level = load_level("two_body_problem", seed=42)
        config = SimulationConfig(enable_interventions=True)
        env = PhyreEnv(level, config=config)
        env.reset()
        env.step([(0, 3, 0.8)])

        # Run for 50 steps
        for _ in range(50):
            env.engine.world.Step(
                env.config.time_step,
                env.config.velocity_iters,
                env.config.position_iters,
            )
            env.engine.time_update(env.config.time_step)

        # Capture state
        snapshot = StateSnapshot.capture(env.engine)

        # Run for 50 more steps
        for _ in range(50):
            env.engine.world.Step(
                env.config.time_step,
                env.config.velocity_iters,
                env.config.position_iters,
            )
            env.engine.time_update(env.config.time_step)

        # Restore to snapshot
        snapshot.restore(env.engine)

        # Verify restoration succeeded (no exception raised)
        # Verify we're back at step 50
        current_snapshot = StateSnapshot.capture(env.engine)
        assert abs(current_snapshot.current_time - snapshot.current_time) < 1e-6

    def test_restore_different_level_fails(self):
        """Test that restore fails when level doesn't match."""
        level1 = load_level("two_body_problem", seed=42)
        level2 = load_level("basket_case", seed=42)

        config = SimulationConfig(enable_interventions=True)

        # Create snapshot from level1
        env1 = PhyreEnv(level1, config=config)
        env1.reset()
        env1.step([(0, 3, 0.8)])
        snapshot1 = StateSnapshot.capture(env1.engine)

        # Try to restore to level2
        env2 = PhyreEnv(level2, config=config)
        env2.reset()

        with pytest.raises(ValueError, match="different level"):
            snapshot1.restore(env2.engine)


class TestStateSnapshotDeterminism:
    """Test deterministic behavior of snapshots."""

    def test_capture_restore_determinism(self):
        """Test that capture→run→restore→run produces same results."""
        level = load_level("two_body_problem", seed=42)
        config = SimulationConfig(enable_interventions=True)

        # First run
        env1 = PhyreEnv(level, config=config)
        env1.reset()
        env1.step([(0, 3, 0.8)])

        # Run to step 50 and capture
        for _ in range(50):
            env1.engine.world.Step(
                env1.config.time_step,
                env1.config.velocity_iters,
                env1.config.position_iters,
            )
            env1.engine.time_update(env1.config.time_step)

        snapshot = StateSnapshot.capture(env1.engine)

        # Run 100 more steps
        for _ in range(100):
            env1.engine.world.Step(
                env1.config.time_step,
                env1.config.velocity_iters,
                env1.config.position_iters,
            )
            env1.engine.time_update(env1.config.time_step)

        snapshot_after_100 = StateSnapshot.capture(env1.engine)

        # Second run: restore and run 100 steps
        snapshot.restore(env1.engine)

        for _ in range(100):
            env1.engine.world.Step(
                env1.config.time_step,
                env1.config.velocity_iters,
                env1.config.position_iters,
            )
            env1.engine.time_update(env1.config.time_step)

        snapshot_after_restore = StateSnapshot.capture(env1.engine)

        # Compare states - should be identical
        assert snapshot_after_100 == snapshot_after_restore

    def test_multiple_capture_restore_cycles(self):
        """Test that multiple capture/restore cycles maintain determinism."""
        level = load_level("catapult", seed=42)
        config = SimulationConfig(enable_interventions=True)
        env = PhyreEnv(level, config=config)
        env.reset()
        env.step([(0, 3, 0.8)])

        snapshots = []

        # Capture at steps 0, 25, 50, 75, 100
        for i in range(5):
            for _ in range(25):
                env.engine.world.Step(
                    env.config.time_step,
                    env.config.velocity_iters,
                    env.config.position_iters,
                )
                env.engine.time_update(env.config.time_step)
            snapshots.append(StateSnapshot.capture(env.engine))

        # Restore to each snapshot and verify state
        for snapshot in snapshots:
            snapshot.restore(env.engine)
            current = StateSnapshot.capture(env.engine)
            assert current == snapshot


class TestStateSnapshotObjectTypes:
    """Test snapshot capture for different object types."""

    def test_capture_ball_objects(self):
        """Test snapshot captures Ball object state correctly."""
        level = load_level("two_body_problem", seed=42)
        config = SimulationConfig(enable_interventions=True)
        env = PhyreEnv(level, config=config)
        env.reset()
        env.step([(0, 3, 0.8)])

        snapshot = StateSnapshot.capture(env.engine)

        # Verify ball objects are captured
        for obj_name, obj_state in snapshot.objects.items():
            assert "position" in obj_state
            assert "velocity" in obj_state
            assert "angle" in obj_state
            assert "angular_velocity" in obj_state
            assert "type" in obj_state
            assert "dynamic" in obj_state

    def test_capture_bar_objects(self):
        """Test snapshot captures Bar object state correctly."""
        level = load_level("catapult", seed=42)
        config = SimulationConfig(enable_interventions=True)
        env = PhyreEnv(level, config=config)
        env.reset()
        env.step([(0, 3, 0.8)])

        snapshot = StateSnapshot.capture(env.engine)

        # Check that Bar objects are present and captured
        bar_objects = [
            obj for obj, state in snapshot.objects.items() if state["type"] == "Bar"
        ]
        assert len(bar_objects) > 0, "Level should contain Bar objects"

    def test_capture_basket_objects(self):
        """Test snapshot captures Basket object state correctly."""
        level = load_level("basket_case", seed=42)
        config = SimulationConfig(enable_interventions=True)
        env = PhyreEnv(level, config=config)
        env.reset()
        env.step([(0, 3, 0.8)])

        snapshot = StateSnapshot.capture(env.engine)

        # Check that Basket objects are present and captured
        basket_objects = [
            obj for obj, state in snapshot.objects.items() if state["type"] == "Basket"
        ]
        assert len(basket_objects) > 0, "Level should contain Basket objects"


class TestStateSnapshotContacts:
    """Test contact state preservation in snapshots."""

    def test_capture_preserves_contacts(self):
        """Test that active contacts are preserved in snapshot."""
        level = load_level("two_body_problem", seed=42)
        config = SimulationConfig(enable_interventions=True)
        env = PhyreEnv(level, config=config)
        env.reset()
        env.step([(0, 3, 0.8)])

        # Run until we have contacts
        for _ in range(100):
            env.engine.world.Step(
                env.config.time_step,
                env.config.velocity_iters,
                env.config.position_iters,
            )
            env.engine.time_update(env.config.time_step)

            if len(env.engine.contact_listener.contacts) > 0:
                break

        snapshot = StateSnapshot.capture(env.engine)

        # Verify contacts captured
        if len(env.engine.contact_listener.contacts) > 0:
            assert len(snapshot.contacts) > 0

    def test_restore_preserves_contacts(self):
        """Test that contacts are restored correctly."""
        level = load_level("two_body_problem", seed=42)
        config = SimulationConfig(enable_interventions=True)
        env = PhyreEnv(level, config=config)
        env.reset()
        env.step([(0, 3, 0.8)])

        # Run until we have contacts
        for _ in range(100):
            env.engine.world.Step(
                env.config.time_step,
                env.config.velocity_iters,
                env.config.position_iters,
            )
            env.engine.time_update(env.config.time_step)

            if len(env.engine.contact_listener.contacts) > 0:
                break

        contacts_before = set(env.engine.contact_listener.contacts)
        snapshot = StateSnapshot.capture(env.engine)

        # Run more steps
        for _ in range(50):
            env.engine.world.Step(
                env.config.time_step,
                env.config.velocity_iters,
                env.config.position_iters,
            )
            env.engine.time_update(env.config.time_step)

        # Restore
        snapshot.restore(env.engine)

        contacts_after = set(env.engine.contact_listener.contacts)

        # Contacts should match
        assert contacts_before == contacts_after


class TestStateSnapshotSerialization:
    """Test snapshot serialization and deserialization."""

    def test_to_bytes_from_bytes_roundtrip(self):
        """Test that to_bytes/from_bytes preserves snapshot."""
        level = load_level("two_body_problem", seed=42)
        config = SimulationConfig(enable_interventions=True)
        env = PhyreEnv(level, config=config)
        env.reset()
        env.step([(0, 3, 0.8)])

        snapshot = StateSnapshot.capture(env.engine)

        # Serialize and deserialize
        snapshot_bytes = snapshot.to_bytes()
        snapshot_restored = StateSnapshot.from_bytes(snapshot_bytes)

        # Should be equal
        assert snapshot == snapshot_restored

    def test_serialized_snapshot_can_restore(self):
        """Test that serialized/deserialized snapshot can restore state."""
        level = load_level("two_body_problem", seed=42)
        config = SimulationConfig(enable_interventions=True)
        env = PhyreEnv(level, config=config)
        env.reset()
        env.step([(0, 3, 0.8)])

        # Run to step 50
        for _ in range(50):
            env.engine.world.Step(
                env.config.time_step,
                env.config.velocity_iters,
                env.config.position_iters,
            )
            env.engine.time_update(env.config.time_step)

        snapshot = StateSnapshot.capture(env.engine)

        # Serialize and deserialize
        snapshot_bytes = snapshot.to_bytes()
        snapshot_restored = StateSnapshot.from_bytes(snapshot_bytes)

        # Run more steps
        for _ in range(50):
            env.engine.world.Step(
                env.config.time_step,
                env.config.velocity_iters,
                env.config.position_iters,
            )
            env.engine.time_update(env.config.time_step)

        # Restore from deserialized snapshot
        snapshot_restored.restore(env.engine)

        # Verify state matches original snapshot
        current = StateSnapshot.capture(env.engine)
        assert abs(current.current_time - snapshot.current_time) < 1e-6


class TestStateSnapshotMetadata:
    """Test metadata handling in snapshots."""

    def test_capture_with_metadata(self):
        """Test that metadata is preserved in snapshot."""
        level = load_level("two_body_problem", seed=42)
        config = SimulationConfig(enable_interventions=True)
        env = PhyreEnv(level, config=config)
        env.reset()
        env.step([(0, 3, 0.8)])

        metadata = {
            "experiment_id": "test_001",
            "trial_number": 42,
            "condition": "factual",
        }

        snapshot = StateSnapshot.capture(env.engine, metadata=metadata)

        assert snapshot.metadata == metadata

    def test_metadata_preserved_in_serialization(self):
        """Test that metadata survives serialization/deserialization."""
        level = load_level("two_body_problem", seed=42)
        config = SimulationConfig(enable_interventions=True)
        env = PhyreEnv(level, config=config)
        env.reset()
        env.step([(0, 3, 0.8)])

        metadata = {"test": "data", "number": 123}
        snapshot = StateSnapshot.capture(env.engine, metadata=metadata)

        # Serialize and deserialize
        snapshot_bytes = snapshot.to_bytes()
        snapshot_restored = StateSnapshot.from_bytes(snapshot_bytes)

        assert snapshot_restored.metadata == metadata
