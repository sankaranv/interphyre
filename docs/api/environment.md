# Gymnasium Environment

## PhyreEnv

`PhyreEnv` is a Gymnasium-compatible environment that runs a one-shot simulation after placing action objects.

Construction:

```python
from interphyre.environment import PhyreEnv
from interphyre.levels import load_level

level = load_level("two_body_problem")
env = PhyreEnv(level, observation_type="physics_state", action_type="continuous")
```

Key parameters:

- `observation_type`: `"physics_state"`, `"image"`, or `"both"`
- `action_type`: `"continuous"` or `"discrete"`
- `image_size`, `image_ppm`, `discrete_colors`
- `renderer`: optional renderer (Pygame or OpenCV)
- `config`: optional `SimulationConfig`

Core methods:

- `reset(seed=None, options=None)`
- `step(action)`
- `simulate(action)`
- `render()`
- `close()`
- `get_level_info()`
- `get_contact_log()`, `get_contact_statistics()`

Notes:

- The environment places all action objects and then runs the physics rollout to completion.
- Discrete actions use 0.1 resolution for x, y, and size bins.
