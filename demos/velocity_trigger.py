#!/usr/bin/env python3
"""
Demo: Velocity-based intervention with automatic triggering.

This demo shows how to use the velocity trigger to catch a fast-moving object
before it escapes the scene. We compare two branches:
- Factual: Object moves fast and escapes
- Counterfactual: Barrier added when velocity exceeds threshold, object is caught
"""

from __future__ import annotations

from interphyre import Box2DEngine
from interphyre.config import SimulationConfig
from interphyre.interventions import (
    CallableIntervention,
    SimulationTrajectory,
    StateSnapshot,
    on_velocity_threshold,
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


def capture_at_high_velocity(
    engine: Box2DEngine,
    obj_name: str,
    speed_threshold: float = 3.0,
    max_steps: int = 240,
) -> StateSnapshot | None:
    """
    Run simulation until object exceeds velocity threshold.

    Args:
        engine: Box2DEngine instance
        obj_name: Name of object to monitor
        speed_threshold: Speed threshold to trigger on
        max_steps: Maximum steps to simulate

    Returns:
        StateSnapshot when trigger fires, or None if timeout
    """
    trigger = on_velocity_threshold(obj_name, speed_threshold=speed_threshold, above=True)

    for step_index in range(max_steps):
        step_engine(engine)
        if trigger.should_fire(step_index + 1, engine):
            body = engine.bodies[obj_name]
            velocity = body.linearVelocity
            speed = (velocity.x**2 + velocity.y**2) ** 0.5
            return StateSnapshot.capture(
                engine,
                metadata={
                    "trigger": "high_velocity",
                    "object": obj_name,
                    "step_index": step_index + 1,
                    "speed": speed,
                },
            )
    return None


def add_barrier_intervention(x: float, y: float, length: float = 2.0) -> CallableIntervention:
    """
    Create an intervention that adds a horizontal barrier.

    Args:
        x: X position of barrier center
        y: Y position of barrier center
        length: Length of barrier

    Returns:
        CallableIntervention that adds the barrier
    """

    def _add_barrier(engine: Box2DEngine) -> None:
        # Add a static bar as a barrier
        from interphyre.objects import Bar

        bar = Bar(x=x, y=y, length=length, thickness=0.3, angle=0, is_dynamic=False)
        engine._create_bar(bar, name="barrier")

    return CallableIntervention(_add_barrier, name="add_barrier")


def main() -> None:
    """Run the velocity trigger demonstration."""
    # Load a level with a fast-moving object
    # We'll use two_body_problem and give the green ball an initial velocity boost
    level = load_level("two_body_problem", seed=1)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    # Give green_ball a velocity boost to make it move fast
    if "green_ball" in engine.bodies:
        from Box2D import b2Vec2

        engine.bodies["green_ball"].linearVelocity = b2Vec2(4.0, 2.0)

    # Capture snapshot when ball exceeds velocity threshold
    snapshot = capture_at_high_velocity(engine, "green_ball", speed_threshold=3.0)

    if snapshot is None:
        print("No high-velocity event detected within max steps.")
        return

    print(f"\n=== Velocity Trigger Fired ===")
    print(f"Step: {snapshot.metadata['step_index']}")
    print(f"Object: {snapshot.metadata['object']}")
    print(f"Speed: {snapshot.metadata['speed']:.2f}")

    # Run factual branch (no intervention)
    steps_after = 120
    factual = SimulationTrajectory(snapshot=snapshot, metadata={"branch": "factual"})
    factual.execute(engine, steps_after)
    factual_success = engine.level.success_condition(engine)

    # Check if ball escaped (went far off screen)
    factual_final_pos = None
    if "green_ball" in engine.bodies:
        body = engine.bodies["green_ball"]
        factual_final_pos = (body.position.x, body.position.y)

    # Run counterfactual branch (add barrier to catch the ball)
    counterfactual = SimulationTrajectory(
        snapshot=snapshot,
        metadata={"branch": "counterfactual_barrier"},
    )

    # Add barrier in front of the ball's trajectory
    if "green_ball" in engine.bodies:
        body = engine.bodies["green_ball"]
        barrier_x = body.position.x + 2.0  # Place barrier ahead
        barrier_y = body.position.y
        counterfactual.apply_intervention(add_barrier_intervention(barrier_x, barrier_y))

    counterfactual.execute(engine, steps_after)
    counterfactual_success = engine.level.success_condition(engine)

    # Check if ball was stopped by barrier
    counterfactual_final_pos = None
    if "green_ball" in engine.bodies:
        body = engine.bodies["green_ball"]
        counterfactual_final_pos = (body.position.x, body.position.y)

    # Print results
    print(f"\n=== Results ===")
    print(f"Factual (no barrier):")
    print(f"  Success: {factual_success}")
    if factual_final_pos:
        print(f"  Final position: ({factual_final_pos[0]:.2f}, {factual_final_pos[1]:.2f})")

    print(f"\nCounterfactual (with barrier):")
    print(f"  Success: {counterfactual_success}")
    if counterfactual_final_pos:
        print(
            f"  Final position: ({counterfactual_final_pos[0]:.2f}, {counterfactual_final_pos[1]:.2f})"
        )

    # Calculate distance traveled
    if factual_final_pos and counterfactual_final_pos:
        factual_dist = (factual_final_pos[0] ** 2 + factual_final_pos[1] ** 2) ** 0.5
        counterfactual_dist = (
            counterfactual_final_pos[0] ** 2 + counterfactual_final_pos[1] ** 2
        ) ** 0.5
        print(f"\nDistance from origin:")
        print(f"  Factual: {factual_dist:.2f}")
        print(f"  Counterfactual: {counterfactual_dist:.2f}")
        print(f"  Difference: {abs(factual_dist - counterfactual_dist):.2f}")


if __name__ == "__main__":
    main()
