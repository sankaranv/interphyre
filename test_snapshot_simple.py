"""
Simple test for State Snapshot functionality.

Tests basic capture/restore using Box2DEngine directly.
"""

from interphyre.engine import Box2DEngine
from interphyre.config import SimulationConfig
from interphyre.interventions import StateSnapshot
from interphyre.levels import load_level


def test_basic_capture_restore():
    """Test basic snapshot capture and restore."""
    print("Test 1: Basic capture and restore...")

    level = load_level("two_body_problem", seed=42)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    # Place action objects
    engine.place_action_objects([(0, 3, 0.8)])

    # Run for 50 steps
    for _ in range(50):
        engine.world.Step(
            config.time_step,
            config.velocity_iters,
            config.position_iters,
        )
        engine.time_update(config.time_step)

    # Capture state
    snapshot = StateSnapshot.capture(engine)
    print(f"  Captured: {snapshot}")

    # Get object state before continuing
    green_ball = engine.bodies.get("green_ball")
    if green_ball:
        pos_before = (green_ball.position.x, green_ball.position.y)
        vel_before = (green_ball.linearVelocity.x, green_ball.linearVelocity.y)
        print(f"  Before: pos={pos_before}, vel={vel_before}")

    # Run 50 more steps
    for _ in range(50):
        engine.world.Step(
            config.time_step,
            config.velocity_iters,
            config.position_iters,
        )
        engine.time_update(config.time_step)

    if green_ball:
        pos_after_100 = (green_ball.position.x, green_ball.position.y)
        print(f"  After 50 more steps: pos={pos_after_100}")

    # Restore
    snapshot.restore(engine)

    if green_ball:
        pos_restored = (green_ball.position.x, green_ball.position.y)
        vel_restored = (green_ball.linearVelocity.x, green_ball.linearVelocity.y)
        print(f"  Restored: pos={pos_restored}, vel={vel_restored}")

        # Verify match
        pos_diff = ((pos_before[0] - pos_restored[0])**2 + (pos_before[1] - pos_restored[1])**2)**0.5
        vel_diff = ((vel_before[0] - vel_restored[0])**2 + (vel_before[1] - vel_restored[1])**2)**0.5

        assert pos_diff < 1e-6, f"Position mismatch: {pos_diff}"
        assert vel_diff < 1e-6, f"Velocity mismatch: {vel_diff}"

        print(f"  ✓ Match confirmed (pos_diff={pos_diff:.2e}, vel_diff={vel_diff:.2e})")

    print("  ✓ Test 1 PASSED\n")


def test_determinism():
    """Test deterministic replay."""
    print("Test 2: Deterministic replay...")

    level = load_level("two_body_problem", seed=42)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)
    engine.place_action_objects([(0, 3, 0.8)])

    # Run to step 50
    for _ in range(50):
        engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
        engine.time_update(config.time_step)

    snapshot_50 = StateSnapshot.capture(engine)

    # Run to step 150
    for _ in range(100):
        engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
        engine.time_update(config.time_step)

    snapshot_150_first = StateSnapshot.capture(engine)
    print(f"  First run: {snapshot_150_first}")

    # Restore and run again
    snapshot_50.restore(engine)

    for _ in range(100):
        engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
        engine.time_update(config.time_step)

    snapshot_150_second = StateSnapshot.capture(engine)
    print(f"  Second run: {snapshot_150_second}")

    # Should be equal
    if snapshot_150_first != snapshot_150_second:
        print(f"\n  Contacts first: {snapshot_150_first.contacts}")
        print(f"  Contacts second: {snapshot_150_second.contacts}")
        print(f"  Contact diff: {snapshot_150_first.contacts.symmetric_difference(snapshot_150_second.contacts)}")

        # Check objects
        for obj_name in snapshot_150_first.objects:
            obj1 = snapshot_150_first.objects[obj_name]
            obj2 = snapshot_150_second.objects[obj_name]
            if obj1 != obj2:
                print(f"  Object '{obj_name}' differs:")
                print(f"    First:  {obj1}")
                print(f"    Second: {obj2}")

        raise AssertionError("Not deterministic!")

    print("  ✓ Determinism confirmed")
    print("  ✓ Test 2 PASSED\n")


def test_serialization():
    """Test snapshot serialization."""
    print("Test 3: Serialization...")

    level = load_level("two_body_problem", seed=42)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)
    engine.place_action_objects([(0, 3, 0.8)])

    # Run some steps
    for _ in range(50):
        engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
        engine.time_update(config.time_step)

    # Capture with metadata
    snapshot = StateSnapshot.capture(engine, metadata={"test": "data", "num": 123})

    # Serialize
    snapshot_bytes = snapshot.to_bytes()
    print(f"  Serialized: {len(snapshot_bytes)} bytes")

    # Deserialize
    snapshot_restored = StateSnapshot.from_bytes(snapshot_bytes)

    # Verify
    assert snapshot == snapshot_restored, "Serialization failed!"
    assert snapshot.metadata == snapshot_restored.metadata, "Metadata lost!"

    print("  ✓ Serialization works")
    print("  ✓ Test 3 PASSED\n")


def test_multiple_levels():
    """Test on multiple levels."""
    print("Test 4: Multiple levels...")

    levels = ["two_body_problem", "catapult"]

    for level_name in levels:
        try:
            level = load_level(level_name, seed=42)
            config = SimulationConfig(enable_interventions=True)
            engine = Box2DEngine(level, config)
            engine.place_action_objects([(0, 3, 0.8)])

            # Run and snapshot
            for _ in range(25):
                engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
                engine.time_update(config.time_step)

            snapshot = StateSnapshot.capture(engine)
            snapshot.restore(engine)

            print(f"  ✓ {level_name}")

        except Exception as e:
            print(f"  ✗ {level_name}: {e}")
            raise

    print("  ✓ Test 4 PASSED\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 1: State Snapshot Tests")
    print("=" * 60)
    print()

    try:
        test_basic_capture_restore()
        test_determinism()
        test_serialization()
        test_multiple_levels()

        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
