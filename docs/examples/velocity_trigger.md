# Velocity Trigger Example

Velocity-based intervention using speed thresholds to automatically detect and react to fast-moving objects.

## Overview

Demonstrates the `on_velocity_threshold()` trigger for speed-based event detection.

**Complexity:** Beginner-Intermediate
**Runtime:** ~1-2 seconds

## Key Concept

```python
from interphyre.interventions import on_velocity_threshold, run_until

# Trigger when ball exceeds speed threshold
trigger = on_velocity_threshold("green_ball", speed_threshold=3.0, above=True)
snapshot, step = run_until(engine, trigger)

# Add barrier to catch the fast ball
if snapshot:
    snapshot.restore(engine)
    add_barrier(engine, x=ball_pos.x + 2.0, y=ball_pos.y)
```

## Running the Example

```bash
python demos/velocity_trigger.py
```

## Use Cases

- Catching fast-moving objects
- Detecting when objects come to rest (`above=False`)
- Speed-based interventions
- Automatic threshold detection

## See Also

- [Branching Event](branching_event.md) - Contact-based triggers
- [Sequence Detection](sequence_detection.md) - Sequential patterns
