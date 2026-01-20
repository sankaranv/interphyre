# Replanning

The core multi-turn agent workflow - run until events, capture state, restore, and continue.

## Overview

This example demonstrates the replanning pattern:

- `run_until(trigger, action=...)` - Run simulation until event
- `restore(snapshot)` - Return to captured state
- `step_until(trigger)` - Continue simulation until next event
- The observe-decide-act loop for multi-turn control

**Complexity:** Intermediate
**Runtime:** ~2 seconds

## Key Concepts

### Multi-Turn Control

Unlike single-shot RL where one action runs to completion, replanning allows:

1. Run until interesting event
2. Observe state
3. Decide whether to intervene
4. Continue or restart

### run_until(trigger, action=None, max_steps=240)

Run simulation until trigger fires or max_steps reached.

```python
snapshot, step = env.run_until(
    on_contact("green_ball", "blue_ball"),
    action=(0.5, 3.0, 0.5),  # Optional: place action object
    max_steps=500
)
```

Returns:

- `snapshot`: State at trigger, or `None` if max_steps reached
- `step`: Step number when trigger fired (or max_steps)

### restore(snapshot)

Return simulation to captured state.

```python
env.restore(snapshot)
# Simulation is now at the exact state when snapshot was taken
```

### step_until(trigger, max_steps=240)

Continue simulation (no new action) until trigger.

```python
# Continue from current state until success
snapshot, step = env.step_until(on_success(), max_steps=300)
```

## Replanning Pattern

The core workflow:

```python
env = PhyreEnv("level", seed=42, enable_interventions=True)

# Phase 1: Run until first event
snapshot, step = env.run_until(
    at_step(50),
    action=(0.5, 3.0, 0.5)
)
env.restore(snapshot)

# Phase 2: Observe and decide
pos = env.engine.bodies["green_ball"].position
if pos.y < 0:
    # Intervene
    env.apply_impulse("green_ball", (0, 5))

# Phase 3: Continue to next checkpoint
snapshot, step = env.step_until(at_step(100))
env.restore(snapshot)

# Phase 4: Continue to completion
snapshot, step = env.step_until(on_success(), max_steps=300)
if snapshot:
    print("Success!")
```

## Code Example

```python
#!/usr/bin/env python3
"""Replanning: Multi-turn control workflow."""

from interphyre import PhyreEnv
from interphyre.interventions import at_step, on_success


def main():
    env = PhyreEnv("two_body_problem", seed=42, enable_interventions=True)

    # === PHASE 1: Run to first checkpoint ===
    print("Phase 1: Running to step 50...")
    snapshot, step = env.run_until(
        at_step(50),
        action=(0.5, 3.0, 0.5),
        max_steps=100
    )

    if not snapshot:
        print("Failed to reach checkpoint")
        env.close()
        return

    print(f"Checkpoint reached at step {step}")

    # === PHASE 2: Observe and decide ===
    env.restore(snapshot)
    green_pos = env.engine.bodies["green_ball"].position
    print(f"green_ball position: ({green_pos.x:.2f}, {green_pos.y:.2f})")

    # Decision: if ball is falling, give it an upward boost
    green_vel = env.engine.bodies["green_ball"].linearVelocity
    if green_vel.y < 0:
        print("Ball is falling - applying upward impulse")
        env.apply_impulse("green_ball", impulse=(0, 8))

    # === PHASE 3: Continue to next checkpoint ===
    print("\nPhase 2: Continuing to step 100...")
    snapshot, step = env.step_until(at_step(100), max_steps=100)

    if snapshot:
        env.restore(snapshot)
        green_pos = env.engine.bodies["green_ball"].position
        print(f"green_ball position: ({green_pos.x:.2f}, {green_pos.y:.2f})")

    # === PHASE 4: Run to completion ===
    print("\nPhase 3: Running to completion...")
    snapshot, step = env.step_until(on_success(), max_steps=300)

    if snapshot:
        print(f"Level solved at step {step}!")
    else:
        print(f"Level not solved (ran {step} steps)")

    env.close()
```

## Running the Example

```bash
python demos/05_replanning.py
```

## Expected Output

```
==================================================
MULTI-TURN REPLANNING DEMONSTRATION
==================================================

Phase 1: Initial placement and run to checkpoint
----------------------------------------
Running until step 50...
Checkpoint reached at step 50
green_ball position: (0.34, 2.15)
green_ball velocity: (0.12, -1.89)

Phase 2: Observe, decide, intervene
----------------------------------------
Ball is falling (vy < 0)
Applying upward impulse...
New velocity: (0.12, 6.11)

Phase 3: Continue to next checkpoint
----------------------------------------
Running until step 100...
Checkpoint reached at step 100
green_ball position: (0.45, 3.21)

Phase 4: Run to completion
----------------------------------------
Running until success or max steps...
Final step: 240
Success: False

==================================================
Replanning workflow demonstrated!
==================================================
```

## Advanced Patterns

### Multiple Attempts

```python
for attempt in range(10):
    snapshot, step = env.run_until(at_step(50), action=sample_action())
    env.restore(snapshot)

    # Analyze and adjust
    if promising(env):
        # Continue this attempt
        env.step_until(on_success(), max_steps=300)
    # Otherwise: loop tries new action
```

### Branching Exploration

```python
# Save early state
snapshot_early, _ = env.run_until(at_step(30), action=action)

for strategy in [impulse_left, impulse_right, no_action]:
    env.restore(snapshot_early)
    strategy(env)
    _, step = env.step_until(on_success(), max_steps=300)
    print(f"{strategy.__name__}: step={step}")
```

## Use Cases

- **Replanning agents:** Pause, observe, decide, continue
- **Monte Carlo Tree Search:** Branch from intermediate states
- **Debugging:** Step through simulation at key points
- **Interactive exploration:** Manual control with checkpoints

## See Also

- [Triggers](triggers.md) - Event types for run_until/step_until
- [Interventions](interventions.md) - Actions to take at checkpoints
- [Counterfactuals](counterfactuals.md) - Compare intervention branches
- [API: Interventions](../api/interventions.md) - Full reference
