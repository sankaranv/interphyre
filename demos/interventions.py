#!/usr/bin/env python3
"""
Interventions: Modifying simulations mid-flight.

Interventions let you change the physics state during simulation:
- Set any attribute on an existing object (radius, length, position, velocity, ...)
- Add/remove objects
- Apply impulses and forces
- Non-destructive counterfactual scope with env.branch(snapshot)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from interphyre import InterphyreEnv
from interphyre.interventions import at_step
from interphyre.objects import Ball


def demo_set():
    """Set attributes on an existing object."""
    print("\n1. env.set()")

    env = InterphyreEnv("two_body_problem", seed=42, enable_interventions=True)
    snapshot, _ = env.run_until(at_step(50), action=(0.5, 3.0, 0.5), max_steps=100)
    env.restore(snapshot)

    before = env.engine.bodies["green_ball"].linearVelocity
    print(f"   Before velocity: ({before.x:.2f}, {before.y:.2f})")

    env.set("green_ball", velocity=(5.0, -3.0))

    after = env.engine.bodies["green_ball"].linearVelocity
    print(f"   After velocity:  ({after.x:.2f}, {after.y:.2f})")
    env.close()


def demo_set_structural():
    """Set a structural property (triggers body recreation)."""
    print("\n2. env.set() structural (radius)")

    env = InterphyreEnv("two_body_problem", seed=42, enable_interventions=True)
    snapshot, _ = env.run_until(at_step(50), action=(0.5, 3.0, 0.5), max_steps=100)
    env.restore(snapshot)

    old_r = env.engine.bodies["green_ball"].fixtures[0].shape.radius
    print(f"   Before radius: {old_r:.2f}")

    env.set("green_ball", radius=0.8)

    new_r = env.engine.bodies["green_ball"].fixtures[0].shape.radius
    print(f"   After radius:  {new_r:.2f}")
    env.close()


def demo_add_remove():
    """Add a new object and then remove it."""
    print("\n3. env.add() / env.remove()")

    env = InterphyreEnv("two_body_problem", seed=42, enable_interventions=True)
    snapshot, _ = env.run_until(at_step(50), action=(0.5, 3.0, 0.5), max_steps=100)
    env.restore(snapshot)

    env.add("extra_ball", Ball(x=2.0, y=3.0, radius=0.3, color="blue", dynamic=True))
    print("   Added extra_ball")
    assert "extra_ball" in env.engine.bodies

    env.remove("extra_ball")
    print("   Removed extra_ball")
    assert "extra_ball" not in env.engine.bodies

    env.close()


def demo_impulse():
    """Apply an instantaneous impulse."""
    print("\n4. env.impulse()")

    env = InterphyreEnv("two_body_problem", seed=42, enable_interventions=True)
    snapshot, _ = env.run_until(at_step(50), action=(0.5, 3.0, 0.5), max_steps=100)
    env.restore(snapshot)

    before = env.engine.bodies["green_ball"].linearVelocity
    print(f"   Before: ({before.x:.2f}, {before.y:.2f})")

    env.impulse("green_ball", (10.0, 5.0))

    after = env.engine.bodies["green_ball"].linearVelocity
    print(f"   After:  ({after.x:.2f}, {after.y:.2f})")
    env.close()


def demo_branch():
    """Non-destructive counterfactual scope."""
    print("\n5. env.branch()")

    env = InterphyreEnv("two_body_problem", seed=42, enable_interventions=True)
    snapshot, step = env.run_until(at_step(50), action=(0.5, 3.0, 0.5), max_steps=100)

    results = {}
    for r in [0.3, 0.6, 1.0]:
        with env.branch(snapshot):
            env.set("green_ball", radius=r)
            env.step_physics(100)
            results[r] = env.success

    print(f"   Results by radius: {results}")
    # World is at snapshot state after the loop
    env.close()


def main():
    print("Interventions Demo")

    demo_set()
    demo_set_structural()
    demo_add_remove()
    demo_impulse()
    demo_branch()


if __name__ == "__main__":
    main()
