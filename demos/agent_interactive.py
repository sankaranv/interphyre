#!/usr/bin/env python3
"""
Demo: Interactive agent with multi-turn replanning.

This demo showcases the three replanning patterns available in the agent API:
1. run_until() - Simple explicit control
2. SimulationIterator - Stateful object for complex loops
3. simulate_with_breaks() - Generator pattern

The scenario: Agent tries to solve a physics puzzle by replanning at critical
moments (contacts, velocity changes) and applying interventions.
"""

from __future__ import annotations

from interphyre import Box2DEngine
from interphyre.config import SimulationConfig
from interphyre.interventions import (
    CallableIntervention,
    on_contact,
    on_velocity_threshold,
    on_success,
    run_until,
    SimulationIterator,
    simulate_with_breaks,
    branch_and_compare,
)
from interphyre.levels import load_level


def create_impulse_intervention(obj_name: str, impulse_x: float, impulse_y: float):
    """Create intervention that applies impulse to object."""

    def _apply(engine: Box2DEngine) -> None:
        if obj_name in engine.bodies:
            from Box2D import b2Vec2

            body = engine.bodies[obj_name]
            body.ApplyLinearImpulse(b2Vec2(impulse_x, impulse_y), body.worldCenter, True)

    return CallableIntervention(_apply, name=f"impulse_{obj_name}")


def create_add_ball_intervention(x: float, y: float, radius: float = 0.5):
    """Create intervention that adds a helper ball."""

    def _add(engine: Box2DEngine) -> None:
        engine.place_action_objects([(x, y, radius)])

    return CallableIntervention(_add, name="add_helper_ball")


def demo_pattern_1_run_until():
    """
    Pattern 1: run_until() - Simple explicit control.

    Best for: Basic replanning, single pause points
    """
    print("\n" + "=" * 70)
    print("PATTERN 1: run_until() - Simple Replanning")
    print("=" * 70)

    level = load_level("two_body_problem", seed=2)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    print("\n[Agent] Starting simulation...")
    print("[Agent] Waiting for first contact event...")

    # Run until first contact
    snapshot, step = run_until(engine, on_contact("green_ball", "blue_ball"), max_steps=240)

    if not snapshot:
        print("[Agent] No contact detected. Task failed.")
        return

    print(f"[Agent] Contact detected at step {step}!")
    print("[Agent] Analyzing situation...")

    # Check if we're on track for success
    success_before = engine.level.success_condition(engine)
    print(f"[Agent] Success before intervention: {success_before}")

    if not success_before:
        print("[Agent] Not on track. Trying intervention: Apply upward impulse to green ball")

        # Restore and apply intervention
        snapshot.restore(engine)
        impulse_intervention = create_impulse_intervention("green_ball", 0, 5.0)
        impulse_intervention.apply(engine)

        # Continue simulation
        snapshot2, step2 = run_until(engine, on_success(), start_step=step, max_steps=120)

        success_after = engine.level.success_condition(engine)
        print(f"[Agent] Success after intervention: {success_after}")
        print(f"[Agent] Final step: {step2}")
    else:
        print("[Agent] Already on track for success. No intervention needed.")


def demo_pattern_2_iterator():
    """
    Pattern 2: SimulationIterator - Stateful control.

    Best for: Complex multi-turn loops, need to track state
    """
    print("\n" + "=" * 70)
    print("PATTERN 2: SimulationIterator - Multi-Turn Replanning")
    print("=" * 70)

    level = load_level("two_body_problem", seed=3)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    # Set up triggers for multiple decision points
    triggers = [
        on_contact("green_ball", "blue_ball"),
        on_velocity_threshold("green_ball", speed_threshold=0.5, above=False),  # Slowing down
        on_success(),
    ]

    sim = SimulationIterator(engine, triggers, max_steps=300)
    intervention_count = 0

    print("\n[Agent] Starting multi-turn simulation...")
    print(f"[Agent] Monitoring {len(triggers)} trigger conditions")

    while sim.current_step < sim.max_steps:
        trigger, snapshot = sim.run_until_next_trigger()

        if trigger is None:
            print(f"[Agent] Simulation timeout at step {sim.current_step}")
            break

        print(f"\n[Agent] Step {sim.current_step}: Trigger fired - {trigger}")

        # Check if it's success trigger
        if "success" in str(trigger).lower():
            print("[Agent] Success achieved! Task complete.")
            break

        # Agent decides whether to intervene
        intervention_count += 1

        if intervention_count == 1:
            print("[Agent] First critical moment - trying impulse intervention")
            snapshot.restore(engine)
            create_impulse_intervention("green_ball", 2.0, 3.0).apply(engine)
        elif intervention_count == 2:
            print("[Agent] Second critical moment - trying helper ball")
            snapshot.restore(engine)
            if "blue_ball" in engine.bodies:
                blue_pos = engine.bodies["blue_ball"].position
                create_add_ball_intervention(blue_pos.x + 1.0, blue_pos.y + 1.0).apply(engine)

    print(f"\n[Agent] Simulation complete. Total interventions: {intervention_count}")
    print(f"[Agent] Trigger history: {len(sim.get_trigger_history())} events")


def demo_pattern_3_generator():
    """
    Pattern 3: simulate_with_breaks() - Generator pattern.

    Best for: Event-driven replanning, clean iteration
    """
    print("\n" + "=" * 70)
    print("PATTERN 3: simulate_with_breaks() - Event-Driven Replanning")
    print("=" * 70)

    level = load_level("two_body_problem", seed=4)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    triggers = [
        on_contact("green_ball", "blue_ball"),
        on_velocity_threshold("green_ball", speed_threshold=1.0, above=False),
    ]

    print("\n[Agent] Starting event-driven simulation...")
    print("[Agent] Will replan at each trigger point")

    event_count = 0

    for step, trigger, snapshot in simulate_with_breaks(engine, triggers, max_steps=240):
        event_count += 1
        print(f"\n[Agent] Event {event_count} at step {step}: {trigger}")

        # Simple decision: alternate between two strategies
        if event_count == 1:
            print("[Agent] Strategy: Boost velocity")
            snapshot.restore(engine)
            create_impulse_intervention("green_ball", 1.0, 2.0).apply(engine)
        elif event_count == 2:
            print("[Agent] Strategy: Add helper object")
            snapshot.restore(engine)
            if "blue_ball" in engine.bodies:
                blue_pos = engine.bodies["blue_ball"].position
                create_add_ball_intervention(blue_pos.x, blue_pos.y + 2.0, 0.4).apply(engine)

        # Limit number of replanning steps
        if event_count >= 3:
            print("[Agent] Maximum replannings reached. Continuing to completion.")
            break

    # Run to completion
    success = engine.level.success_condition(engine)
    print(f"\n[Agent] Final result: {'Success' if success else 'Failure'}")
    print(f"[Agent] Total replanning events: {event_count}")


def demo_branch_comparison():
    """
    Bonus: Compare multiple intervention strategies from same point.
    """
    print("\n" + "=" * 70)
    print("BONUS: Branch Comparison - Test Multiple Strategies")
    print("=" * 70)

    level = load_level("two_body_problem", seed=5)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    # Run to first contact
    snapshot, step = run_until(engine, on_contact("green_ball", "blue_ball"), max_steps=240)

    if not snapshot:
        print("[Agent] No branch point found.")
        return

    print(f"\n[Agent] Found branch point at step {step}")
    print("[Agent] Testing 3 different intervention strategies...")

    # Test multiple strategies
    strategies = [
        create_impulse_intervention("green_ball", 0, 5.0),
        create_impulse_intervention("green_ball", 3.0, 2.0),
        create_add_ball_intervention(0, 3.0, 0.6),
    ]

    results = branch_and_compare(snapshot, strategies, steps=120, include_factual=True)

    print(f"\n[Agent] Results from {len(results)} branches:")
    for i, result in enumerate(results):
        branch_name = result.metadata.get("branch", f"branch_{i}")
        print(
            f"  {branch_name}: {'SUCCESS' if result.success else 'FAILURE'} "
            f"(final_step={result.final_step})"
        )

    # Find best strategy
    successful_branches = [r for r in results if r.success]
    if successful_branches:
        print(f"\n[Agent] ✓ Found {len(successful_branches)} successful strategies!")
    else:
        print("\n[Agent] ✗ No strategy succeeded. Need to try different approaches.")


def main():
    """Run all demo patterns."""
    print("\n" + "=" * 70)
    print("INTERACTIVE AGENT REPLANNING DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo shows three patterns for multi-turn simulation with replanning:")
    print("  1. run_until() - Simple explicit control")
    print("  2. SimulationIterator - Stateful object for complex loops")
    print("  3. simulate_with_breaks() - Pythonic generator pattern")
    print("  + Branch comparison for strategy evaluation")

    try:
        demo_pattern_1_run_until()
        demo_pattern_2_iterator()
        demo_pattern_3_generator()
        demo_branch_comparison()

        print("\n" + "=" * 70)
        print("DEMONSTRATION COMPLETE")
        print("=" * 70)
        print("\nAll patterns successfully demonstrated!")
        print("Choose the pattern that best fits your research needs:")
        print("  - Simple single-pause: use run_until()")
        print("  - Complex multi-turn: use SimulationIterator")
        print("  - Event processing: use simulate_with_breaks()")

    except Exception as e:
        print(f"\n[Error] Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
