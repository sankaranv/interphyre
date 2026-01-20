# Counterfactuals

Causal analysis with branching simulations - compare "what happened" vs "what could have happened".

## Overview

This example demonstrates:

- Capturing state at a branch point
- Running factual branch (no intervention)
- Restoring and running counterfactual branch (with intervention)
- Comparing outcomes to measure causal effect

**Complexity:** Advanced
**Runtime:** ~2 seconds

## Key Concepts

### Counterfactual Reasoning

"Would the outcome have been different if I had intervened?"

This is the core question in causal inference. Interphyre enables precise counterfactual analysis by:

1. Running simulation to an event of interest
2. Capturing exact state
3. Running two (or more) branches with different interventions
4. Comparing outcomes

### Causal Effect

The difference between counterfactual and factual outcomes:

```python
causal_effect = int(counterfactual_success) - int(factual_success)
# +1 = intervention helped
# -1 = intervention hurt
#  0 = no difference
```

### Branch Point

The moment where you capture state and diverge into multiple trajectories.

```python
# Wait for interesting event
snapshot, step = env.run_until(on_contact("a", "b"), action=...)

# This snapshot is the branch point
# Everything before is shared history
# Everything after diverges
```

## Branching Pattern

```python
env = PhyreEnv("level", seed=0, enable_interventions=True)

# Run to branch point
trigger = on_contact("green_ball", "blue_ball")
snapshot, step = env.run_until(trigger, action=action, max_steps=500)

if not snapshot:
    print("Event never occurred")
    return

# === FACTUAL BRANCH ===
env.restore(snapshot)
for _ in range(200):
    env._step_physics()
factual_success = env.success
factual_position = get_position(env, "green_ball")

# === COUNTERFACTUAL BRANCH ===
env.restore(snapshot)  # Back to same point
env.apply_impulse("green_ball", (10, 5))  # Different action
for _ in range(200):
    env._step_physics()
counterfactual_success = env.success
counterfactual_position = get_position(env, "green_ball")

# === ANALYSIS ===
causal_effect = int(counterfactual_success) - int(factual_success)
position_divergence = distance(factual_position, counterfactual_position)
```

## Code Example

```python
#!/usr/bin/env python3
"""Counterfactuals: Compare 'what happened' vs 'what could have happened'."""

from interphyre import PhyreEnv
from interphyre.interventions import on_contact


def main():
    env = PhyreEnv("two_body_problem", seed=0, enable_interventions=True)

    # Run until green and blue balls contact
    trigger = on_contact("green_ball", "blue_ball")
    snapshot, step = env.run_until(trigger, action=(-4.5, 4.5, 0.5), max_steps=500)

    if not snapshot:
        print("Balls never contacted")
        env.close()
        return

    print(f"Branch point: contact at step {step}")

    # === FACTUAL BRANCH ===
    env.restore(snapshot)
    for _ in range(200):
        env._step_physics()

    factual_success = env.success
    factual_pos = (
        env.engine.bodies["green_ball"].position.x,
        env.engine.bodies["green_ball"].position.y,
    )
    print(f"Factual: success={factual_success}, pos={factual_pos}")

    # === COUNTERFACTUAL BRANCH ===
    env.restore(snapshot)
    env.apply_impulse("green_ball", impulse=(10.0, 5.0))

    for _ in range(200):
        env._step_physics()

    counterfactual_success = env.success
    counterfactual_pos = (
        env.engine.bodies["green_ball"].position.x,
        env.engine.bodies["green_ball"].position.y,
    )
    print(f"Counterfactual: success={counterfactual_success}, pos={counterfactual_pos}")

    # === CAUSAL ANALYSIS ===
    causal_effect = int(counterfactual_success) - int(factual_success)
    dx = counterfactual_pos[0] - factual_pos[0]
    dy = counterfactual_pos[1] - factual_pos[1]
    divergence = (dx**2 + dy**2) ** 0.5

    print(f"\nCausal effect: {causal_effect:+d}")
    print(f"Position divergence: {divergence:.2f} units")

    env.close()
```

## Running the Example

```bash
python demos/06_counterfactuals.py
```

## Expected Output

```
Counterfactual Analysis Demo
==================================================

[Setup] Level: two_body_problem
[Setup] Trigger: on_contact('green_ball', 'blue_ball')
[Setup] Running until trigger fires...

[Branch Point] Contact occurred at step 343
[Branch Point] Captured state for branching.

[Factual] Running without intervention...
[Factual] Final green_ball position: (-3.45, -4.12)
[Factual] Success: False

[Counterfactual] Restoring to branch point...
[Counterfactual] Applied impulse (10, 5) to green_ball
[Counterfactual] Final green_ball position: (2.34, -2.89)
[Counterfactual] Success: False

==================================================
CAUSAL ANALYSIS
==================================================
Factual outcome:       FAILURE
Counterfactual outcome: FAILURE
Causal effect: 0 (no difference)
Position divergence: 5.89 units (dx=5.79, dy=1.23)
```

## Multiple Counterfactuals

Test several interventions:

```python
interventions = [
    ("no_action", lambda e: None),
    ("impulse_left", lambda e: e.apply_impulse("green_ball", (-10, 0))),
    ("impulse_right", lambda e: e.apply_impulse("green_ball", (10, 0))),
    ("impulse_up", lambda e: e.apply_impulse("green_ball", (0, 10))),
    ("freeze", lambda e: e.freeze("green_ball")),
]

results = {}
for name, intervention in interventions:
    env.restore(snapshot)
    intervention(env)
    run_to_completion(env)
    results[name] = env.success

# Compare all outcomes
for name, success in results.items():
    print(f"{name}: {'SUCCESS' if success else 'FAILURE'}")
```

## Use Cases

- **Causal discovery:** Which objects/events matter for success?
- **Strategy comparison:** Which intervention is most effective?
- **Sensitivity analysis:** How robust is a solution to perturbations?
- **Debugging:** Why did a solution fail?

## Research Applications

### Necessary Causation

"Was event X necessary for outcome Y?"

```python
# Factual: X happened, Y happened
# Counterfactual: remove X, does Y still happen?
if factual_Y and not counterfactual_Y:
    print("X was necessary for Y")
```

### Sufficient Causation

"Was event X sufficient for outcome Y?"

```python
# Try adding X in situations where it wasn't present
# Does Y consistently follow?
```

### Causal Chains

Use `on_sequence()` to identify causal chains:

```python
trigger = on_sequence([
    on_contact("red", "green"),
    on_contact("green", "blue"),
])
# Branch after first contact vs after second
```

## See Also

- [Triggers](triggers.md) - Define branch points
- [Interventions](interventions.md) - Available modifications
- [Replanning](replanning.md) - Multi-turn control
- [API: Interventions](../api/interventions.md) - Full reference
