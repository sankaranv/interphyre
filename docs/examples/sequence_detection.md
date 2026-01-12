# Sequence Detection Example

Sequential event pattern detection for causal chains where events must occur in specific order.

## Overview

Demonstrates the `on_sequence()` trigger for detecting multi-step event patterns.

**Complexity:** Intermediate
**Runtime:** ~3-4 seconds

## Key Concept

```python
from interphyre.interventions import on_sequence, on_contact, run_until

# Fire only when events occur in order
sequence_trigger = on_sequence([
    on_contact("green_ball", "blue_ball"),
    on_contact("blue_ball", "red_ball")
], reset_on_failure=True)

snapshot, step = run_until(engine, sequence_trigger)
```

## Features Demonstrated

- **Sequential patterns:** A must happen before B before C
- **Reset behavior:** Sequence resets if events fire out of order
- **Event history:** Record and analyze all events
- **Causal chains:** Test temporal dependencies

## Running the Example

```bash
python demos/sequence_detection.py
```

## Use Cases

- Causal chain detection ("A causes B causes C")
- Multi-step puzzle solving
- Temporal dependency analysis
- Complex event processing

## See Also

- [Agent Interactive](agent_interactive.md) - Multi-turn replanning
- [API: Triggers](../api/interventions.md#triggers) - All trigger types
