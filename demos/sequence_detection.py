#!/usr/bin/env python3
"""
Demo: Sequential event pattern detection with causal chains.

This demo showcases the on_sequence() trigger, which fires only when events
occur in a specific order. This is useful for:
- Causal chain detection (A must happen before B before C)
- Multi-step puzzle solving
- Temporal dependencies in physics

Scenario: We detect when ball A contacts B, then B contacts C in sequence.
Only when this chain occurs do we intervene.
"""

from __future__ import annotations

from interphyre import Box2DEngine
from interphyre.config import SimulationConfig
from interphyre.interventions import (
    CallableIntervention,
    SimulationTrajectory,
    StateSnapshot,
    on_contact,
    on_contact_with,
    on_sequence,
    record_simulation,
    run_until,
)
from interphyre.levels import load_level


def step_engine(engine: Box2DEngine) -> None:
    """Execute a single physics step."""
    engine.world.Step(
        engine.config.time_step,
        engine.config.velocity_iters,
        engine.config.position_iters,
    )
    engine.time_update(engine.config.time_step)


def create_celebration_intervention():
    """Create intervention that celebrates sequence completion."""

    def _celebrate(engine: Box2DEngine) -> None:
        # Add a celebratory object when sequence completes
        print("  [Intervention] Sequence completed! Adding celebration marker...")
        engine.place_action_objects([(5.0, 5.0, 0.3)])

    return CallableIntervention(_celebrate, name="celebrate_sequence")


def demo_basic_sequence():
    """
    Basic sequence detection: A→B then B→C.
    """
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Sequential Pattern Detection")
    print("=" * 70)

    level = load_level("two_body_problem", seed=10)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    print("\n[Setup] Defining sequence: green_ball→blue_ball, then blue_ball→<any>")

    # Define sequence trigger
    sequence_trigger = on_sequence(
        [
            on_contact("green_ball", "blue_ball", once_only=True),
            on_contact_with("blue_ball", once_only=True),  # blue contacts anything after
        ],
        reset_on_failure=True,
    )

    print("[Running] Simulating until sequence completes...")

    # Run until sequence fires
    snapshot, step = run_until(engine, sequence_trigger, max_steps=300)

    if snapshot:
        print(f"\n[Success] Sequence completed at step {step}!")
        print(f"[Info] Captured snapshot with metadata: {snapshot.metadata}")
    else:
        print("\n[Timeout] Sequence did not complete within max steps.")


def demo_sequence_with_branching():
    """
    Compare outcomes with and without intervention after sequence.
    """
    print("\n" + "=" * 70)
    print("DEMO 2: Sequence Detection + Branching")
    print("=" * 70)

    level = load_level("two_body_problem", seed=11)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    # Define contact sequence
    sequence_trigger = on_sequence(
        [
            on_contact("green_ball", "blue_ball"),
            on_contact_with("blue_ball"),  # Any second contact involving blue_ball
        ]
    )

    print("\n[Running] Waiting for contact sequence...")

    snapshot, step = run_until(engine, sequence_trigger, max_steps=300)

    if not snapshot:
        print("[Timeout] Sequence not detected.")
        return

    print(f"\n[Detected] Sequence fired at step {step}!")
    print("[Analysis] Comparing factual vs. counterfactual branches...")

    # Factual: Continue without intervention
    factual_traj = SimulationTrajectory(snapshot=snapshot, metadata={"branch": "factual"})
    factual_traj.execute(engine, steps=120)
    factual_success = engine.level.success_condition(engine)

    # Counterfactual: Apply intervention when sequence completes
    counterfactual_traj = SimulationTrajectory(
        snapshot=snapshot, metadata={"branch": "counterfactual"}
    )
    counterfactual_traj.apply_intervention(create_celebration_intervention())
    counterfactual_traj.execute(engine, steps=120)
    counterfactual_success = engine.level.success_condition(engine)

    print(f"\n[Results]")
    print(f"  Factual (no intervention):       {'SUCCESS' if factual_success else 'FAILURE'}")
    print(
        f"  Counterfactual (with intervention): {'SUCCESS' if counterfactual_success else 'FAILURE'}"
    )

    causal_effect = float(counterfactual_success) - float(factual_success)
    print(f"  Causal effect: {causal_effect:+.1f}")


def demo_sequence_with_history():
    """
    Record all events and analyze sequence patterns.
    """
    print("\n" + "=" * 70)
    print("DEMO 3: Sequence Detection + Event History")
    print("=" * 70)

    level = load_level("two_body_problem", seed=12)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    # Record all contact events
    all_contact_triggers = [
        on_contact("green_ball", "blue_ball", once_only=False),
        on_contact_with("blue_ball", once_only=False),
        on_contact_with("green_ball", once_only=False),
    ]

    print("\n[Recording] Running simulation and recording all contact events...")

    history = record_simulation(engine, all_contact_triggers, max_steps=300, max_events=20)

    print(f"\n[Recorded] {len(history)} events")
    print(f"[Summary] {history.summary()}")

    if len(history) > 0:
        print(f"\n[Event Timeline]")
        for event in history.events[:10]:  # Show first 10
            print(f"  Step {event.step_index:3d}: {event.trigger}")

        # Check if we can find a sequence pattern
        print(f"\n[Analysis] Searching for sequential patterns...")

        contact_events = history.filter_by_type("contact")
        if len(contact_events) >= 2:
            print(f"  Found {len(contact_events)} contact events")
            print(f"  First contact:  Step {contact_events[0].step_index}")
            print(f"  Second contact: Step {contact_events[1].step_index}")

            time_diff = contact_events[1].step_index - contact_events[0].step_index
            print(f"  Time between:   {time_diff} steps")


def demo_complex_sequence():
    """
    Three-step sequence with reset behavior.
    """
    print("\n" + "=" * 70)
    print("DEMO 4: Complex Three-Step Sequence")
    print("=" * 70)

    level = load_level("two_body_problem", seed=13)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    print("\n[Setup] Three-step sequence with reset_on_failure=True")
    print("        If events fire out of order, sequence resets.")

    # Define three-step sequence
    sequence_trigger = on_sequence(
        [
            on_contact("green_ball", "blue_ball"),
            on_contact_with("blue_ball"),
            on_contact_with("green_ball"),
        ],
        reset_on_failure=True,  # Reset if out of order
    )

    print("\n[Running] Waiting for three-step sequence...")

    snapshot, step = run_until(engine, sequence_trigger, max_steps=400)

    if snapshot:
        print(f"\n[Success] Three-step sequence completed at step {step}!")
        print("[Info] All three contacts occurred in the correct order.")
    else:
        print("\n[Timeout] Sequence did not complete.")
        print("[Info] Events may have occurred out of order, causing resets.")


def main():
    """Run all sequence detection demos."""
    print("\n" + "=" * 70)
    print("SEQUENTIAL EVENT PATTERN DETECTION DEMONSTRATION")
    print("=" * 70)
    print("\nShowing the on_sequence() trigger for causal chain detection:")
    print("  - Basic sequence: A contacts B, then B contacts C")
    print("  - Branching after sequence completion")
    print("  - Event history analysis")
    print("  - Complex multi-step sequences with reset")

    try:
        demo_basic_sequence()
        demo_sequence_with_branching()
        demo_sequence_with_history()
        demo_complex_sequence()

        print("\n" + "=" * 70)
        print("DEMONSTRATION COMPLETE")
        print("=" * 70)
        print("\nSequential patterns successfully demonstrated!")
        print("\nUse Cases:")
        print("  - Causal chain detection (A must cause B must cause C)")
        print("  - Multi-step puzzle solving")
        print("  - Temporal dependency analysis")
        print("  - Complex event processing")

    except Exception as e:
        print(f"\n[Error] Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
