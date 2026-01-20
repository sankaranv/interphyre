#!/usr/bin/env python3
"""
Replanning: Multi-turn simulation with checkpoints.

This demo shows the core intervention workflow:
1. Run simulation until an event (trigger)
2. Capture a checkpoint (snapshot)
3. Make modifications (add objects, apply forces)
4. Continue from the checkpoint

This enables agents to observe, decide, and act multiple times.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from interphyre import PhyreEnv
from interphyre.interventions import on_contact, on_success
from interphyre.objects import Ball


def main():
    print("Replanning Demo")
    print("=" * 50)

    # Create environment with interventions enabled
    env = PhyreEnv("catapult", seed=0, enable_interventions=True)

    # Initial action parameters
    action = (-0.25, 2.5, 1.0)

    # Define trigger: wait for green_ball to hit the platform
    trigger = on_contact("green_ball", "black_platform")

    print(f"\n[Step 1] Running with initial action: {action}")
    print(f"[Step 1] Waiting for trigger: {trigger}")

    # Run until the trigger fires, placing the action at the start
    snapshot, step = env.run_until(trigger, action=action, max_steps=500)

    if not snapshot:
        print("[Result] Trigger did not fire within max steps.")
        env.close()
        return

    print(f"\n[Step 2] Trigger fired at step {step}!")
    print("[Step 2] Captured checkpoint for potential replanning.")

    # Restore to the checkpoint
    env.restore(snapshot)
    print("[Step 3] Restored to checkpoint.")

    # Add a new object using intervention context
    with env.intervention_context() as ctx:
        # Add a red ball with an impulse
        ctx.add_object(
            "red_ball_2",
            Ball(x=-2.0, y=-3.0, radius=0.4, color="red", dynamic=True),
        )
        ctx.apply_impulse("red_ball_2", impulse=(5.0, 0.0))

    print("[Step 3] Added red_ball_2 with rightward impulse.")

    # Continue simulation until success or timeout
    remaining = max(500 - step, 0)
    if remaining > 0:
        obs, reward, term, trunc, info = env.step_until(
            on_success(), max_steps=remaining
        )
        success = info["success"]
    else:
        success = env.success

    print(f"\n[Result] Final outcome: {'SUCCESS' if success else 'FAILURE'}")
    print(
        "\nNote: This demo shows the replanning workflow. The specific"
        "\naction may not solve the puzzle - the goal is to demonstrate"
        "\nthe checkpoint/restore/modify pattern."
    )

    env.close()


if __name__ == "__main__":
    main()
