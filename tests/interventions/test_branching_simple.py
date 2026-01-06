"""
Simple tests for Phase 2: Branching Simulations.

Tests branching, counterfactual generation, and branch independence.
"""

from interphyre.engine import Box2DEngine
from interphyre.config import SimulationConfig
from interphyre.interventions import StateSnapshot, SimulationBranch, create_factual_counterfactual_pair
from interphyre.interventions.core import CallableIntervention
from interphyre.levels import load_level


def test_basic_branching():
    """Test basic branch creation and execution."""
    print("Test 1: Basic branching...")

    level = load_level("two_body_problem", seed=42)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)
    engine.place_action_objects([(0, 3, 0.8)])

    # Run to step 50
    for _ in range(50):
        engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
        engine.time_update(config.time_step)

    # Capture snapshot
    snapshot = StateSnapshot.capture(engine)
    print(f"  Captured snapshot at step 50: {snapshot}")

    # Create branch
    branch = SimulationBranch(snapshot=snapshot, metadata={"test": "basic"})
    print(f"  Created branch: {branch}")

    # Execute branch
    result = branch.execute(engine, steps=50)
    print(f"  Executed branch for 50 steps")
    print(f"  Final state: {result['final_snapshot']}")
    print(f"  Branch ID: {result['branch_id'][:8]}")

    assert result['metadata'] == {"test": "basic"}
    assert result['final_snapshot'].step_count == 100

    print("  ✓ Test 1 PASSED\n")


def test_branch_independence():
    """Test that branches are independent of each other."""
    print("Test 2: Branch independence...")

    level = load_level("two_body_problem", seed=42)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)
    engine.place_action_objects([(0, 3, 0.8)])

    # Run to step 50
    for _ in range(50):
        engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
        engine.time_update(config.time_step)

    snapshot = StateSnapshot.capture(engine)

    # Branch A: Run 100 steps
    branch_a = SimulationBranch(snapshot=snapshot, metadata={"branch": "A"})
    result_a = branch_a.execute(engine, steps=100)
    print(f"  Branch A: {result_a['final_snapshot']}")

    # Branch B: Run 50 steps (from same snapshot)
    branch_b = SimulationBranch(snapshot=snapshot, metadata={"branch": "B"})
    result_b = branch_b.execute(engine, steps=50)
    print(f"  Branch B: {result_b['final_snapshot']}")

    # Verify they are independent
    assert result_a['final_snapshot'].step_count == 150
    assert result_b['final_snapshot'].step_count == 100
    assert result_a['branch_id'] != result_b['branch_id']

    print("  ✓ Branch A and B are independent")
    print("  ✓ Test 2 PASSED\n")


def test_branch_with_intervention():
    """Test branch with intervention applied."""
    print("Test 3: Branch with intervention...")

    level = load_level("two_body_problem", seed=42)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)
    engine.place_action_objects([(0, 3, 0.8)])

    # Run to step 50
    for _ in range(50):
        engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
        engine.time_update(config.time_step)

    snapshot = StateSnapshot.capture(engine)

    # Get original green_ball position
    green_ball_before = snapshot.objects["green_ball"]["position"]
    print(f"  Green ball position before: {green_ball_before}")

    # Create intervention to teleport green_ball
    def teleport_intervention(engine):
        if "green_ball" in engine.bodies:
            from Box2D import b2Vec2
            engine.bodies["green_ball"].transform = (b2Vec2(0, 5), 0)
            print(f"    Intervention applied: teleported green_ball to (0, 5)")

    intervention = CallableIntervention(teleport_intervention, name="teleport")

    # Create branch with intervention
    branch = SimulationBranch(snapshot=snapshot)
    branch.apply_intervention(intervention)

    # Execute
    result = branch.execute(engine, steps=1)
    green_ball_after = result["final_snapshot"].objects["green_ball"]["position"]
    print(f"  Green ball position after intervention: {green_ball_after}")

    # Verify intervention was applied
    assert abs(green_ball_after[0] - 0.0) < 0.1, "X position should be near 0"
    assert green_ball_after[1] > 4.0, "Y position should be above 4"

    print("  ✓ Intervention successfully applied")
    print("  ✓ Test 3 PASSED\n")


def test_factual_counterfactual_pair():
    """Test factual/counterfactual pair generation."""
    print("Test 4: Factual/counterfactual pair...")

    level = load_level("two_body_problem", seed=42)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)
    engine.place_action_objects([(0, 3, 0.8)])

    # Run to step 50
    for _ in range(50):
        engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
        engine.time_update(config.time_step)

    snapshot = StateSnapshot.capture(engine)

    # Define counterfactual intervention: boost red_ball upward
    def boost_intervention(engine):
        if "red_ball" in engine.bodies:
            body = engine.bodies["red_ball"]
            from Box2D import b2Vec2
            body.ApplyLinearImpulse(b2Vec2(0, 50), body.worldCenter, True)
            print("    Counterfactual: boosted red_ball upward")

    intervention = CallableIntervention(boost_intervention, name="boost")

    # Generate factual/counterfactual pair
    factual, counterfactual = create_factual_counterfactual_pair(
        engine=engine,
        snapshot=snapshot,
        counterfactual_interventions=[intervention],
        steps=100,
    )

    print(f"  Factual final state: {factual['final_snapshot']}")
    print(f"  Counterfactual final state: {counterfactual['final_snapshot']}")

    # Verify both reached same step count
    assert factual['final_snapshot'].step_count == 150
    assert counterfactual['final_snapshot'].step_count == 150

    # Verify metadata
    assert factual['metadata']['condition'] == "factual"
    assert counterfactual['metadata']['condition'] == "counterfactual"

    # Verify they have different outcomes (intervention made a difference)
    factual_pos = factual['final_snapshot'].objects["red_ball"]["position"]
    counterfactual_pos = counterfactual['final_snapshot'].objects["red_ball"]["position"]

    print(f"  Factual red_ball position: {factual_pos}")
    print(f"  Counterfactual red_ball position: {counterfactual_pos}")

    # Positions should differ due to intervention
    pos_diff = ((factual_pos[0] - counterfactual_pos[0])**2 +
                (factual_pos[1] - counterfactual_pos[1])**2)**0.5
    print(f"  Position difference: {pos_diff:.2f}")

    assert pos_diff > 0.1, "Intervention should cause noticeable difference"

    print("  ✓ Factual and counterfactual successfully generated")
    print("  ✓ Test 4 PASSED\n")


def test_nested_branching():
    """Test creating branches from branches."""
    print("Test 5: Nested branching...")

    level = load_level("two_body_problem", seed=42)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)
    engine.place_action_objects([(0, 3, 0.8)])

    # Run to step 50
    for _ in range(50):
        engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
        engine.time_update(config.time_step)

    snapshot_50 = StateSnapshot.capture(engine)

    # Parent branch
    parent_branch = SimulationBranch(snapshot=snapshot_50, metadata={"level": "parent"})
    result_parent = parent_branch.execute(engine, steps=50)
    snapshot_100 = result_parent["final_snapshot"]

    # Child branch from parent
    child_branch = parent_branch.create_child_branch(
        snapshot=snapshot_100,
        metadata={"level": "child"}
    )

    print(f"  Parent branch: {parent_branch}")
    print(f"  Child branch: {child_branch}")

    # Verify relationship
    assert child_branch.parent_branch == parent_branch
    assert child_branch.metadata["level"] == "child"

    # Get ancestry
    ancestry = child_branch.get_ancestry()
    print(f"  Ancestry chain length: {len(ancestry)}")

    assert len(ancestry) == 2
    assert ancestry[0] == parent_branch
    assert ancestry[1] == child_branch

    print("  ✓ Nested branching works correctly")
    print("  ✓ Test 5 PASSED\n")


def test_branch_with_trace():
    """Test branch execution with full trajectory trace."""
    print("Test 6: Branch with trace...")

    level = load_level("two_body_problem", seed=42)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)
    engine.place_action_objects([(0, 3, 0.8)])

    # Run to step 50
    for _ in range(50):
        engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
        engine.time_update(config.time_step)

    snapshot = StateSnapshot.capture(engine)

    # Execute with trace
    branch = SimulationBranch(snapshot=snapshot)
    result = branch.execute(engine, steps=10, return_trace=True)

    assert "trace" in result
    assert len(result["trace"]) == 11  # Initial + 10 steps

    print(f"  Trace length: {len(result['trace'])}")
    print(f"  First snapshot: {result['trace'][0]}")
    print(f"  Last snapshot: {result['trace'][-1]}")

    # Verify trajectory
    for i, snap in enumerate(result["trace"]):
        expected_step = 50 + i
        assert snap.step_count == expected_step, f"Step {i} should be at {expected_step}"

    print("  ✓ Trace correctly captured")
    print("  ✓ Test 6 PASSED\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 2: Branching Simulations Tests")
    print("=" * 60)
    print()

    try:
        test_basic_branching()
        test_branch_independence()
        test_branch_with_intervention()
        test_factual_counterfactual_pair()
        test_nested_branching()
        test_branch_with_trace()

        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
