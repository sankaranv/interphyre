#!/usr/bin/env python3
"""
Demo: event-driven branching with a mid-simulation action.

This script runs a simulation until a trigger fires, captures a snapshot,
then executes factual vs. counterfactual branches from the same state.
The counterfactual branch adds a red ball at the branch point.
"""

from __future__ import annotations

from interphyre import Box2DEngine
from interphyre.config import SimulationConfig
from interphyre.interventions import (
    CallableIntervention,
    SimulationTrajectory,
    StateSnapshot,
    on_contact,
)
from interphyre.levels import load_level


def step_engine(engine: Box2DEngine) -> None:
    engine.world.Step(
        engine.config.time_step,
        engine.config.velocity_iters,
        engine.config.position_iters,
    )
    engine.time_update(engine.config.time_step)


def capture_branchpoint(
    engine: Box2DEngine,
    max_steps: int = 240,
) -> StateSnapshot | None:
    trigger = on_contact("green_ball", "blue_ball", once_only=True)

    for step_index in range(max_steps):
        step_engine(engine)
        if trigger.should_fire(step_index + 1, engine):
            return StateSnapshot.capture(
                engine,
                metadata={"trigger": "green_blue_contact", "step_index": step_index + 1},
            )
    return None


def spawn_red_ball(x: float, y: float, radius: float) -> CallableIntervention:
    def _spawn(engine: Box2DEngine) -> None:
        # Place the action object mid-simulation (red_ball is an action object in this level).
        engine.place_action_objects([(x, y, radius)])

    return CallableIntervention(_spawn, name="spawn_red_ball")


def main() -> None:
    level = load_level("two_body_problem", seed=0)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    snapshot = capture_branchpoint(engine)
    if snapshot is None:
        print("No branchpoint found within max steps.")
        return

    steps_after = 120

    factual = SimulationTrajectory(snapshot=snapshot, metadata={"branch": "factual"})
    factual.execute(engine, steps_after)
    factual_success = engine.level.success_condition(engine)

    counterfactual = SimulationTrajectory(
        snapshot=snapshot,
        metadata={"branch": "counterfactual_add_red"},
    )
    counterfactual.apply_intervention(spawn_red_ball(x=-3.0, y=2.5, radius=0.6))
    counterfactual.execute(engine, steps_after)
    counterfactual_success = engine.level.success_condition(engine)

    print(
        "Branchpoint step:",
        snapshot.step_index,
        "| factual_success:",
        factual_success,
        "| counterfactual_success:",
        counterfactual_success,
    )


if __name__ == "__main__":
    main()
