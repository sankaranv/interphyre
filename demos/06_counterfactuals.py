#!/usr/bin/env python3
"""
Counterfactuals: Compare "what happened" vs "what could have happened".

This demo shows causal analysis through branching:
1. Run simulation to a branch point
2. Capture state
3. Run factual branch (no intervention)
4. Restore and run counterfactual branch (with intervention)
5. Compare outcomes to measure causal effect

This is useful for understanding which events/objects are causally important.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from interphyre import PhyreEnv
from interphyre.interventions import on_contact
from interphyre.objects import Ball


def main():
    print("Counterfactual Analysis Demo")
    print("=" * 50)

    # Create environment with interventions enabled
    env = PhyreEnv("two_body_problem", seed=0, enable_interventions=True)

    # Wait for green and blue balls to contact
    trigger = on_contact("green_ball", "blue_ball")

    print(f"\n[Setup] Level: two_body_problem")
    print(f"[Setup] Trigger: {trigger}")
    print(f"[Setup] Running until trigger fires...\n")

    # Run until contact, placing a ball that knocks green toward blue
    snapshot, step = env.run_until(trigger, action=(-4.5, 4.5, 0.5), max_steps=500)

    if not snapshot:
        print("[Result] Trigger did not fire - balls never contacted.")
        env.close()
        return

    print(f"[Branch Point] Contact occurred at step {step}")
    print(f"[Branch Point] Captured state for branching.\n")

    # === FACTUAL BRANCH ===
    # Continue from checkpoint without intervention
    print("[Factual] Running without intervention...")
    env.restore(snapshot)

    # Step through remaining simulation
    for _ in range(200):
        env._step_physics()
    factual_success = env.success

    # Record final positions for comparison (capture as tuple to avoid reference issues)
    factual_green_pos = (
        env.engine.bodies["green_ball"].position.x,
        env.engine.bodies["green_ball"].position.y,
    )
    print(f"[Factual] Final green_ball position: ({factual_green_pos[0]:.2f}, {factual_green_pos[1]:.2f})")
    print(f"[Factual] Success: {factual_success}")

    # === COUNTERFACTUAL BRANCH ===
    # Restore and add an intervention
    print("\n[Counterfactual] Restoring to branch point...")
    env.restore(snapshot)

    # Apply impulse to green ball to change its trajectory
    with env.intervention_context() as ctx:
        ctx.apply_impulse("green_ball", impulse=(10.0, 5.0))

    print("[Counterfactual] Applied impulse (10, 5) to green_ball")

    # Run counterfactual branch
    for _ in range(200):
        env._step_physics()
    counterfactual_success = env.success

    counterfactual_green_pos = (
        env.engine.bodies["green_ball"].position.x,
        env.engine.bodies["green_ball"].position.y,
    )
    print(f"[Counterfactual] Final green_ball position: ({counterfactual_green_pos[0]:.2f}, {counterfactual_green_pos[1]:.2f})")
    print(f"[Counterfactual] Success: {counterfactual_success}")

    # === CAUSAL ANALYSIS ===
    print("\n" + "=" * 50)
    print("CAUSAL ANALYSIS")
    print("=" * 50)
    print(f"Factual outcome:       {'SUCCESS' if factual_success else 'FAILURE'}")
    print(f"Counterfactual outcome: {'SUCCESS' if counterfactual_success else 'FAILURE'}")

    causal_effect = int(counterfactual_success) - int(factual_success)
    if causal_effect > 0:
        print(f"Causal effect: +{causal_effect} (intervention helped)")
    elif causal_effect < 0:
        print(f"Causal effect: {causal_effect} (intervention hurt)")
    else:
        print(f"Causal effect: 0 (no difference)")

    # Position difference
    dx = counterfactual_green_pos[0] - factual_green_pos[0]
    dy = counterfactual_green_pos[1] - factual_green_pos[1]
    pos_diff = (dx ** 2 + dy ** 2) ** 0.5
    print(f"Position divergence: {pos_diff:.2f} units (dx={dx:.2f}, dy={dy:.2f})")

    env.close()


if __name__ == "__main__":
    main()
