# Examples

Interactive demonstrations of the Interphyre intervention API for multi-turn simulations, replanning research, and causal inference.

## Available Examples

### [Level Viewer](level_viewer.md)
Explore and visualize PHYRE levels. View individual levels or batch process multiple levels to understand the physics puzzles.

**Use case:** Understanding PHYRE levels, initial exploration

### [Branching Event](branching_event.md)
Event-driven branching with factual and counterfactual trajectories. Shows how to pause simulation at trigger points and branch into multiple outcomes.

**Use case:** Basic causal inference, single-event branching

### [Velocity Trigger](velocity_trigger.md)
Velocity-based intervention using speed thresholds. Automatically detect when objects move fast and intervene to change outcomes.

**Use case:** Speed-based control, catching fast-moving objects

### [Agent Interactive](agent_interactive.md)
Multi-turn replanning with three different patterns. Complete demonstration of all replanning approaches for agent research.

**Use case:** Replanning research, multi-turn decision making

### [Sequence Detection](sequence_detection.md)
Sequential event pattern detection and causal chains. Fire triggers only when events occur in specific order.

**Use case:** Temporal causality, multi-step puzzle solving

## Running Examples

All examples are located in the `demos/` directory:

```bash
# From project root
python demos/level_viewer.py
python demos/branching_event.py
python demos/velocity_trigger.py
python demos/agent_interactive.py
python demos/sequence_detection.py
```

Or using module syntax:
```bash
python -m demos.level_viewer
python -m demos.branching_event
# ...
```

## Learning Path

**New to Interphyre?**

1. Start with [Level Viewer](level_viewer.md) to explore available levels
2. Try [Branching Event](branching_event.md) for intervention basics
3. Learn new triggers with [Velocity Trigger](velocity_trigger.md)
4. Master replanning with [Agent Interactive](agent_interactive.md)
5. Explore advanced patterns with [Sequence Detection](sequence_detection.md)

**For replanning research:**

Focus on [Agent Interactive](agent_interactive.md) which demonstrates three replanning patterns:

- `run_until()` - Simple explicit control
- `SimulationIterator` - Stateful multi-turn loops
- `simulate_with_breaks()` - Generator pattern

**For causal inference:**

Start with [Branching Event](branching_event.md), then explore [Sequence Detection](sequence_detection.md) for temporal causality.
