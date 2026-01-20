#!/usr/bin/env python3
"""
Interventions: Modifying simulations mid-flight.

Interventions let you change the physics state during simulation:
- Add/remove objects
- Apply forces and impulses
- Set velocities and positions
- Freeze objects

Changes can be made directly or via InterventionContext for batching.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from interphyre import PhyreEnv
from interphyre.interventions import at_step
from interphyre.objects import Ball


def demo_add_object():
    """Add a new object during simulation."""
    print("\n1. ADD OBJECT")
    print("-" * 40)

    env = PhyreEnv("two_body_problem", seed=42, enable_interventions=True)

    # Run to step 50
    snapshot, _ = env.run_until(at_step(50), action=(0.5, 3.0, 0.5), max_steps=100)
    env.restore(snapshot)

    # Add a new ball
    env.add_object(
        "new_ball",
        Ball(x=2.0, y=3.0, radius=0.3, color="blue", dynamic=True),
    )

    print("   Added 'new_ball' at (2.0, 3.0)")
    print(f"   Objects now: {list(env.level.objects.keys())}")

    env.close()


def demo_add_with_impulse():
    """Add object and immediately apply impulse."""
    print("\n2. ADD OBJECT WITH IMPULSE")
    print("-" * 40)

    env = PhyreEnv("two_body_problem", seed=42, enable_interventions=True)

    snapshot, _ = env.run_until(at_step(50), action=(0.5, 3.0, 0.5), max_steps=100)
    env.restore(snapshot)

    # Add ball with initial impulse (shorthand)
    env.add_object(
        "fast_ball",
        Ball(x=-2.0, y=2.0, radius=0.4, color="red", dynamic=True),
        impulse=(5.0, 0.0),  # Rightward impulse
    )

    vel = env.engine.bodies["fast_ball"].linearVelocity
    print(f"   Added 'fast_ball' with velocity ({vel.x:.2f}, {vel.y:.2f})")

    env.close()


def demo_apply_impulse():
    """Apply impulse to existing object."""
    print("\n3. APPLY IMPULSE")
    print("-" * 40)

    env = PhyreEnv("two_body_problem", seed=42, enable_interventions=True)

    snapshot, _ = env.run_until(at_step(50), action=(0.5, 3.0, 0.5), max_steps=100)
    env.restore(snapshot)

    before = env.engine.bodies["green_ball"].linearVelocity
    print(f"   green_ball velocity before: ({before.x:.2f}, {before.y:.2f})")

    # Apply impulse
    env.apply_impulse("green_ball", impulse=(10.0, 5.0))

    after = env.engine.bodies["green_ball"].linearVelocity
    print(f"   green_ball velocity after:  ({after.x:.2f}, {after.y:.2f})")

    env.close()


def demo_set_velocity():
    """Set object velocity directly."""
    print("\n4. SET VELOCITY")
    print("-" * 40)

    env = PhyreEnv("two_body_problem", seed=42, enable_interventions=True)

    snapshot, _ = env.run_until(at_step(50), action=(0.5, 3.0, 0.5), max_steps=100)
    env.restore(snapshot)

    # Set exact velocity
    env.set_velocity("green_ball", vx=5.0, vy=-3.0)

    vel = env.engine.bodies["green_ball"].linearVelocity
    print(f"   Set green_ball velocity to ({vel.x:.2f}, {vel.y:.2f})")

    env.close()


def demo_set_position():
    """Teleport object to new position."""
    print("\n5. SET POSITION")
    print("-" * 40)

    env = PhyreEnv("two_body_problem", seed=42, enable_interventions=True)

    snapshot, _ = env.run_until(at_step(50), action=(0.5, 3.0, 0.5), max_steps=100)
    env.restore(snapshot)

    before = env.engine.bodies["green_ball"].position
    print(f"   green_ball position before: ({before.x:.2f}, {before.y:.2f})")

    # Teleport to new position
    env.set_position("green_ball", x=0.0, y=0.0)

    after = env.engine.bodies["green_ball"].position
    print(f"   green_ball position after:  ({after.x:.2f}, {after.y:.2f})")

    env.close()


def demo_freeze():
    """Stop an object completely."""
    print("\n6. FREEZE OBJECT")
    print("-" * 40)

    env = PhyreEnv("two_body_problem", seed=42, enable_interventions=True)

    snapshot, _ = env.run_until(at_step(50), action=(0.5, 3.0, 0.5), max_steps=100)
    env.restore(snapshot)

    before = env.engine.bodies["green_ball"].linearVelocity
    print(f"   green_ball velocity before: ({before.x:.2f}, {before.y:.2f})")

    # Freeze (zero all velocities)
    env.freeze("green_ball")

    after = env.engine.bodies["green_ball"].linearVelocity
    print(f"   green_ball velocity after:  ({after.x:.2f}, {after.y:.2f})")

    env.close()


def demo_intervention_context():
    """Use InterventionContext for multiple changes."""
    print("\n7. INTERVENTION CONTEXT (batched changes)")
    print("-" * 40)

    env = PhyreEnv("two_body_problem", seed=42, enable_interventions=True)

    snapshot, _ = env.run_until(at_step(50), action=(0.5, 3.0, 0.5), max_steps=100)
    env.restore(snapshot)

    # Multiple changes in one context
    with env.intervention_context() as ctx:
        ctx.add_object(
            "helper_ball",
            Ball(x=-3.0, y=3.0, radius=0.5, color="blue", dynamic=True),
        )
        ctx.apply_impulse("helper_ball", impulse=(8.0, 0.0))
        ctx.set_velocity("green_ball", vx=0.0, vy=0.0)  # Stop green ball

    print("   Applied multiple interventions:")
    print("   - Added helper_ball")
    print("   - Applied impulse to helper_ball")
    print("   - Stopped green_ball")

    env.close()


def main():
    print("=" * 50)
    print("INTERVENTION TYPES DEMONSTRATION")
    print("=" * 50)

    demo_add_object()
    demo_add_with_impulse()
    demo_apply_impulse()
    demo_set_velocity()
    demo_set_position()
    demo_freeze()
    demo_intervention_context()

    print("\n" + "=" * 50)
    print("All intervention types demonstrated!")
    print("=" * 50)


if __name__ == "__main__":
    main()
