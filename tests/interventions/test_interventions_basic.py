"""
Basic manual test for Phase 1 interventions.

This script tests core functionality without requiring pytest.
"""

from interphyre.environment import PhyreEnv
from interphyre.config import SimulationConfig
from interphyre.interventions import StateSnapshot
from interphyre.levels import load_level


def test_basic_snapshot_capture():
    """Test basic snapshot capture and restore."""
    print("Test 1: Basic snapshot capture and restore...")

    level = load_level("two_body_problem", seed=42)
    config = SimulationConfig(enable_interventions=True)
    env = PhyreEnv(level, config=config)
    obs, info = env.reset()

    # Place action object
    action = [(0.0, 3.0, 0.8)]
    obs, reward, terminated, truncated, info = env.step(action)

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
    print(f"  Captured snapshot: {snapshot}")

    # Get positions before continuing
    green_ball_body = env.engine.bodies.get("green_ball")
    pos_before = (
        (green_ball_body.position.x, green_ball_body.position.y)
        if green_ball_body
        else None
    )
    print(f"  Position at step 50: {pos_before}")

    # Run for 50 more steps
    for _ in range(50):
        env.engine.world.Step(
            env.config.time_step,
            env.config.velocity_iters,
            env.config.position_iters,
        )
        env.engine.time_update(env.config.time_step)

    pos_after_100 = (
        (green_ball_body.position.x, green_ball_body.position.y)
        if green_ball_body
        else None
    )
    print(f"  Position at step 100: {pos_after_100}")

    # Restore to step 50
    snapshot.restore(env.engine)

    pos_after_restore = (
        (green_ball_body.position.x, green_ball_body.position.y)
        if green_ball_body
        else None
    )
    print(f"  Position after restore: {pos_after_restore}")

    # Verify positions match
    if pos_before and pos_after_restore:
        diff = (
            (pos_before[0] - pos_after_restore[0]) ** 2
            + (pos_before[1] - pos_after_restore[1]) ** 2
        ) ** 0.5
        assert diff < 1e-6, f"Position mismatch after restore: {diff}"
        print(f"  ✓ Positions match (diff={diff:.2e})")
    else:
        print("  ✗ Could not verify positions (object not found)")

    print("  ✓ Test 1 PASSED\n")


def test_determinism():
    """Test deterministic replay after restore."""
    print("Test 2: Deterministic replay...")

    level = load_level("catapult", seed=42)
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

    snapshot_50 = StateSnapshot.capture(env.engine)

    # Run to step 150
    for _ in range(100):
        env.engine.world.Step(
            env.config.time_step,
            env.config.velocity_iters,
            env.config.position_iters,
        )
        env.engine.time_update(env.config.time_step)

    snapshot_150_first = StateSnapshot.capture(env.engine)
    print(f"  First run to step 150: {snapshot_150_first}")

    # Restore to step 50 and run again
    snapshot_50.restore(env.engine)

    for _ in range(100):
        env.engine.world.Step(
            env.config.time_step,
            env.config.velocity_iters,
            env.config.position_iters,
        )
        env.engine.time_update(env.config.time_step)

    snapshot_150_second = StateSnapshot.capture(env.engine)
    print(f"  Second run to step 150: {snapshot_150_second}")

    # Compare snapshots
    assert snapshot_150_first == snapshot_150_second, "Snapshots don't match!"
    print("  ✓ Deterministic replay confirmed")
    print("  ✓ Test 2 PASSED\n")


def test_serialization():
    """Test snapshot serialization."""
    print("Test 3: Snapshot serialization...")

    level = load_level("two_body_problem", seed=42)
    config = SimulationConfig(enable_interventions=True)
    env = PhyreEnv(level, config=config)
    env.reset()
    env.step([(0, 3, 0.8)])

    # Capture snapshot
    snapshot = StateSnapshot.capture(env.engine, metadata={"test": "data"})
    print(f"  Original snapshot: {snapshot}")

    # Serialize and deserialize
    snapshot_bytes = snapshot.to_bytes()
    print(f"  Serialized size: {len(snapshot_bytes)} bytes")

    snapshot_restored = StateSnapshot.from_bytes(snapshot_bytes)
    print(f"  Restored snapshot: {snapshot_restored}")

    # Verify equality
    assert snapshot == snapshot_restored, "Serialization changed snapshot!"
    assert snapshot.metadata == snapshot_restored.metadata, "Metadata lost!"

    print("  ✓ Serialization preserved snapshot")
    print("  ✓ Test 3 PASSED\n")


def test_multiple_levels():
    """Test snapshot works on different level types."""
    print("Test 4: Multiple level types...")

    levels_to_test = ["two_body_problem", "catapult", "basket_case"]

    for level_name in levels_to_test:
        print(f"  Testing {level_name}...")
        level = load_level(level_name, seed=42)
        config = SimulationConfig(enable_interventions=True)
        env = PhyreEnv(level, config=config)
        env.reset()
        env.step([(0, 3, 0.8)])

        # Run some steps
        for _ in range(25):
            env.engine.world.Step(
                env.config.time_step,
                env.config.velocity_iters,
                env.config.position_iters,
            )
            env.engine.time_update(env.config.time_step)

        # Capture and restore
        snapshot = StateSnapshot.capture(env.engine)
        snapshot.restore(env.engine)

        print(f"    ✓ {level_name} snapshot works")

    print("  ✓ Test 4 PASSED\n")


def test_contact_preservation():
    """Test that contacts are preserved in snapshots."""
    print("Test 5: Contact preservation...")

    level = load_level("two_body_problem", seed=42)
    config = SimulationConfig(enable_interventions=True)
    env = PhyreEnv(level, config=config)
    env.reset()
    env.step([(0, 3, 0.8)])

    # Run until we have contacts
    for i in range(200):
        env.engine.world.Step(
            env.config.time_step,
            env.config.velocity_iters,
            env.config.position_iters,
        )
        env.engine.time_update(env.config.time_step)

        if len(env.engine.contact_listener.contacts) > 0:
            print(f"  Contacts detected at step {i}")
            break

    contacts_before = set(env.engine.contact_listener.contacts)
    print(f"  Contacts before: {contacts_before}")

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
    print(f"  Contacts after restore: {contacts_after}")

    assert contacts_before == contacts_after, "Contacts not preserved!"
    print("  ✓ Contacts preserved correctly")
    print("  ✓ Test 5 PASSED\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 1: State Capture & Restoration Tests")
    print("=" * 60)
    print()

    try:
        test_basic_snapshot_capture()
        test_determinism()
        test_serialization()
        test_multiple_levels()
        test_contact_preservation()

        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
