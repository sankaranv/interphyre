"""
Simple integration tests for Phase 6: High-Level API & Research Utilities

Tests the context manager API, helper methods, and experiment utilities.
"""

from interphyre.engine import Box2DEngine
from interphyre.levels import load_level
from interphyre.config import SimulationConfig
from interphyre.interventions import (
    StateSnapshot,
    InterventionContext,
    generate_counterfactual_pairs,
    ExperimentResults,
)


def print_test_header(test_num: int, test_name: str):
    print(f"\nTest {test_num}: {test_name}...")


def test_1_context_manager_basic():
    """Test basic context manager usage."""
    print_test_header(1, "Context manager basic usage")

    level = load_level("two_body_problem")
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    # Get initial position
    initial_pos = engine.bodies["green_ball"].position.copy()

    # Use context manager to modify position
    with InterventionContext(engine) as ctx:
        ctx.set_position("green_ball", x=5.0, y=5.0)

        # Verify modification applied
        new_pos = engine.bodies["green_ball"].position
        assert abs(new_pos.x - 5.0) < 1e-6, f"Expected x=5.0, got {new_pos.x}"
        assert abs(new_pos.y - 5.0) < 1e-6, f"Expected y=5.0, got {new_pos.y}"

    # After context exit, modification persists (no rollback on success)
    final_pos = engine.bodies["green_ball"].position
    assert abs(final_pos.x - 5.0) < 1e-6, "Position should persist after context"

    print("  ✓ Test 1 PASSED")


def test_2_context_manager_rollback():
    """Test automatic rollback on exception."""
    print_test_header(2, "Context manager rollback on exception")

    level = load_level("two_body_problem")
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    # Get initial position
    initial_pos = engine.bodies["green_ball"].position.copy()

    # Try to modify but raise exception
    try:
        with InterventionContext(engine, auto_rollback=True) as ctx:
            ctx.set_position("green_ball", x=5.0, y=5.0)

            # Verify modification applied
            new_pos = engine.bodies["green_ball"].position
            assert abs(new_pos.x - 5.0) < 1e-6

            # Raise exception
            raise ValueError("Test exception")
    except ValueError:
        pass  # Expected

    # After exception, position should be rolled back
    final_pos = engine.bodies["green_ball"].position
    assert abs(final_pos.x - initial_pos.x) < 1e-6, "Position should be rolled back"
    assert abs(final_pos.y - initial_pos.y) < 1e-6, "Position should be rolled back"

    print("  ✓ Test 2 PASSED")


def test_3_helper_methods():
    """Test all helper methods (set_position, set_velocity, etc.)."""
    print_test_header(3, "Helper methods")

    level = load_level("two_body_problem")
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    with InterventionContext(engine, auto_rollback=False) as ctx:
        # Test set_position
        ctx.set_position("green_ball", x=2.0, y=3.0)
        pos = engine.bodies["green_ball"].position
        assert abs(pos.x - 2.0) < 1e-6
        assert abs(pos.y - 3.0) < 1e-6

        # Test set_velocity
        ctx.set_velocity("green_ball", vx=1.5, vy=-2.0)
        vel = engine.bodies["green_ball"].linearVelocity
        assert abs(vel.x - 1.5) < 1e-6
        assert abs(vel.y - (-2.0)) < 1e-6

        # Test scale_velocity
        ctx.scale_velocity("green_ball", factor=2.0)
        vel = engine.bodies["green_ball"].linearVelocity
        assert abs(vel.x - 3.0) < 1e-6  # 1.5 * 2.0
        assert abs(vel.y - (-4.0)) < 1e-6  # -2.0 * 2.0

        # Test set_angle
        ctx.set_angle("green_ball", angle=1.57)  # ~90 degrees
        angle = engine.bodies["green_ball"].angle
        assert abs(angle - 1.57) < 1e-6

        # Test set_angular_velocity
        ctx.set_angular_velocity("green_ball", omega=0.5)
        omega = engine.bodies["green_ball"].angularVelocity
        assert abs(omega - 0.5) < 1e-6

        # Test set_gravity
        ctx.set_gravity((0.0, -5.0))
        gravity = engine.world.gravity
        assert abs(gravity.x - 0.0) < 1e-6
        assert abs(gravity.y - (-5.0)) < 1e-6

        # Test freeze
        ctx.freeze("green_ball")
        vel = engine.bodies["green_ball"].linearVelocity
        omega = engine.bodies["green_ball"].angularVelocity
        assert abs(vel.x) < 1e-6
        assert abs(vel.y) < 1e-6
        assert abs(omega) < 1e-6

    print("  ✓ Test 3 PASSED")


def test_4_method_chaining():
    """Test method chaining for fluent API."""
    print_test_header(4, "Method chaining")

    level = load_level("two_body_problem")
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    with InterventionContext(engine) as ctx:
        # Chain multiple methods
        (
            ctx.set_position("green_ball", x=2.0, y=3.0)
            .set_velocity("green_ball", vx=1.0, vy=-1.0)
            .set_angle("green_ball", angle=0.5)
        )

        # Verify all applied
        pos = engine.bodies["green_ball"].position
        vel = engine.bodies["green_ball"].linearVelocity
        angle = engine.bodies["green_ball"].angle

        assert abs(pos.x - 2.0) < 1e-6
        assert abs(pos.y - 3.0) < 1e-6
        assert abs(vel.x - 1.0) < 1e-6
        assert abs(vel.y - (-1.0)) < 1e-6
        assert abs(angle - 0.5) < 1e-6

    print("  ✓ Test 4 PASSED")


def test_5_modification_tracking():
    """Test modification tracking for reproducibility."""
    print_test_header(5, "Modification tracking")

    level = load_level("two_body_problem")
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    with InterventionContext(engine) as ctx:
        ctx.set_position("green_ball", x=2.0, y=3.0)
        ctx.set_velocity("green_ball", vx=1.0, vy=-1.0)

        # Get modifications
        mods = ctx.get_modifications()

        assert len(mods) == 2, f"Expected 2 modifications, got {len(mods)}"
        assert mods[0]["type"] == "set_position"
        assert mods[0]["object"] == "green_ball"
        assert mods[0]["x"] == 2.0
        assert mods[0]["y"] == 3.0

        assert mods[1]["type"] == "set_velocity"
        assert mods[1]["object"] == "green_ball"
        assert mods[1]["vx"] == 1.0
        assert mods[1]["vy"] == -1.0

    print("  ✓ Test 5 PASSED")


def test_6_counterfactual_intervention():
    """Test InterventionContext with auto_rollback=False for counterfactuals."""
    print_test_header(6, "Counterfactual intervention")

    level = load_level("two_body_problem")
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    # Run to step 50
    for _ in range(50):
        engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
        engine.time_update(config.time_step)

    # Capture snapshot
    snapshot = StateSnapshot.capture(engine)

    # Factual branch - continue without intervention
    for _ in range(50):
        engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
        engine.time_update(config.time_step)

    factual_step = int(round(engine.contact_listener.current_time / config.time_step))

    # Counterfactual branch - apply intervention
    snapshot.restore(engine)

    with InterventionContext(engine, auto_rollback=False) as ctx:
        ctx.set_velocity("green_ball", vx=5.0, vy=0.0)

    for _ in range(50):
        engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
        engine.time_update(config.time_step)

    cf_step = int(round(engine.contact_listener.current_time / config.time_step))

    # Both should end at step 100
    assert factual_step == 100
    assert cf_step == 100

    print("  ✓ Test 6 PASSED")


def test_7_experiment_results():
    """Test ExperimentResults aggregation."""
    print_test_header(7, "ExperimentResults aggregation")

    results = ExperimentResults()

    # Add trials
    results.add_trial({"success": True, "score": 10.0})
    results.add_trial({"success": False, "score": 5.0})
    results.add_trial({"success": True, "score": 8.0})

    # Test aggregation
    assert results.get_success_rate() == 2 / 3, "Success rate should be 2/3"
    assert abs(results.get_mean("score") - 7.666) < 0.01, "Mean score should be ~7.67"

    # Test summary
    summary = results.summary()
    assert summary["num_trials"] == 3
    assert "score_mean" in summary
    assert "score_std" in summary
    assert "success_rate" in summary

    print("  ✓ Test 7 PASSED")


def test_8_generate_counterfactual_pairs():
    """Test generate_counterfactual_pairs utility."""
    print_test_header(8, "Generate counterfactual pairs")

    def make_engine():
        level = load_level("two_body_problem")
        config = SimulationConfig(enable_interventions=True)
        return Box2DEngine(level, config)

    def boost_velocity(engine):
        body = engine.bodies["green_ball"]
        from Box2D import b2Vec2

        body.linearVelocity = b2Vec2(
            body.linearVelocity.x * 1.5, body.linearVelocity.y * 1.5
        )

    pairs = generate_counterfactual_pairs(
        engine_factory=make_engine,
        intervention_step=30,
        interventions=[boost_velocity],
        simulation_steps=100,
        num_trials=2,
        seed=42,
    )

    assert len(pairs) == 2, f"Expected 2 pairs, got {len(pairs)}"

    for pair in pairs:
        assert "success" in pair.factual_result
        assert "success" in pair.counterfactual_result
        assert pair.snapshot is not None

        # Test causal effect computation
        effect = pair.causal_effect("success")
        assert isinstance(effect, (int, float))

    print("  ✓ Test 8 PASSED")


def test_9_apply_impulse():
    """Test apply_impulse helper method."""
    print_test_header(9, "Apply impulse")

    level = load_level("two_body_problem")
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    # Get initial velocity
    initial_vel = engine.bodies["green_ball"].linearVelocity.copy()

    with InterventionContext(engine) as ctx:
        # Apply upward impulse
        ctx.apply_impulse("green_ball", impulse=(0.0, 10.0))

        # Verify velocity changed
        new_vel = engine.bodies["green_ball"].linearVelocity
        assert new_vel.y > initial_vel.y, "Velocity should increase after impulse"

    print("  ✓ Test 9 PASSED")


def test_10_error_handling():
    """Test error handling for invalid objects."""
    print_test_header(10, "Error handling")

    level = load_level("two_body_problem")
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    try:
        with InterventionContext(engine) as ctx:
            ctx.set_position("nonexistent_object", x=1.0, y=2.0)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not found" in str(e).lower()
        assert "available objects" in str(e).lower(), "Error should list available objects"

    print("  ✓ Test 10 PASSED")


def main():
    print("=" * 60)
    print("Phase 6: High-Level API & Research Utilities Tests")
    print("=" * 60)

    test_1_context_manager_basic()
    test_2_context_manager_rollback()
    test_3_helper_methods()
    test_4_method_chaining()
    test_5_modification_tracking()
    test_6_counterfactual_intervention()
    test_7_experiment_results()
    test_8_generate_counterfactual_pairs()
    test_9_apply_impulse()
    test_10_error_handling()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()
