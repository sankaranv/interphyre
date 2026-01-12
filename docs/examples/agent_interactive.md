# Agent Interactive Example

Comprehensive multi-turn replanning demonstration showing three different patterns for interactive agents.

## Overview

This example demonstrates:

- Three replanning patterns: `run_until()`, `SimulationIterator`, `simulate_with_breaks()`
- Multi-turn decision making
- Branch comparison for strategy evaluation
- Iterative problem solving

**Complexity:** Intermediate-Advanced
**Runtime:** ~3-5 seconds

## Three Replanning Patterns

### Pattern 1: run_until()

Simple explicit control for single pause points.

```python
from interphyre.interventions import run_until, on_contact

# Run until contact
snapshot, step = run_until(engine, on_contact("ball", "wall"))

if snapshot:
    # Agent decides to intervene
    snapshot.restore(engine)
    apply_intervention(engine)

    # Continue from where we left off
    snapshot2, step2 = run_until(engine, on_success(), start_step=step)
```

**When to use:** Simple single-pause replanning, explicit step management

### Pattern 2: SimulationIterator

Stateful iteration for complex multi-turn scenarios.

```python
from interphyre.interventions import SimulationIterator

sim = SimulationIterator(engine, [
    on_contact("ball", "wall"),
    on_velocity_threshold("ball", 0.1),
    on_success()
])

while sim.current_step < sim.max_steps:
    trigger, snapshot = sim.run_until_next_trigger()

    if trigger is None:
        break

    # Agent replans
    snapshot.restore(engine)
    apply_intervention(engine)
```

**When to use:** Multiple decision points, need to track history, complex control flow

### Pattern 3: simulate_with_breaks()

Generator pattern for event-driven processing.

```python
from interphyre.interventions import simulate_with_breaks

for step, trigger, snapshot in simulate_with_breaks(engine, triggers):
    if should_intervene(trigger):
        snapshot.restore(engine)
        apply_intervention(engine)
```

**When to use:** Event-driven processing, Pythonic iteration, functional style

## Branch Comparison

Test multiple strategies from the same point:

```python
from interphyre.interventions import branch_and_compare

# Capture critical moment
snapshot, step = run_until(engine, on_contact("ball", "wall"))

# Try multiple strategies
strategies = [
    impulse_intervention,
    add_ball_intervention,
    gravity_intervention
]

results = branch_and_compare(snapshot, strategies, steps=120)

# Find best strategy
for i, result in enumerate(results):
    print(f"Strategy {i}: {'SUCCESS' if result.success else 'FAILURE'}")
```

## Running the Example

```bash
python demos/agent_interactive.py
```

## Expected Output

```
=== PATTERN 1: run_until() ===
Contact detected at step 42
Intervention applied
Success achieved

=== PATTERN 2: SimulationIterator ===
Event 1 at step 38: Contact
Event 2 at step 95: Velocity threshold
Total interventions: 2

=== PATTERN 3: simulate_with_breaks() ===
Processing event at step 45
Processing event at step 103
Final result: SUCCESS

=== BONUS: Branch Comparison ===
Testing 3 strategies...
  factual: FAILURE
  counterfactual_0: SUCCESS
  counterfactual_1: FAILURE
  counterfactual_2: SUCCESS
```

## Use Cases

- **Replanning research:** Multi-turn agent experiments
- **Strategy evaluation:** Compare multiple intervention approaches
- **Interactive problem solving:** Agent observes, decides, acts iteratively
- **Tool-calling agents:** Pause-replan-continue loops

## Pattern Selection Guide

| Need | Use Pattern |
|------|-------------|
| Single pause point | `run_until()` |
| Multiple decision points | `SimulationIterator` |
| Event processing | `simulate_with_breaks()` |
| Strategy comparison | `branch_and_compare()` |

## See Also

- [Branching Event](branching_event.md) - Simpler single-branch example
- [Sequence Detection](sequence_detection.md) - Complex event patterns
- [API: Replanning](../api/interventions.md#replanning) - Full API reference
