# Getting Started

This is a minimal entry point based on `tools/demo.py` to load a level, place an action, and run a full simulation rollout.

## Minimal example

```python
from interphyre.levels import load_level
from interphyre.environment import PhyreEnv
from interphyre.render.pygame import PygameRenderer
from interphyre.config import SimulationConfig

# Load a level (seed is optional)
level = load_level("basket_case", seed=0)

# Create config + renderer
config = SimulationConfig(fps=60, time_step=1 / 60)
renderer = PygameRenderer(width=600, height=600, ppm=60)

# Build the environment
env = PhyreEnv(level=level, renderer=renderer, config=config)

# Reset and run a single rollout
obs, info = env.reset()

# Actions are (x, y, size) per action object
# basket_case has one action object ("red_ball")
action = [0.0, 0.0, 0.5]
obs, reward, terminated, truncated, info = env.step(action)

print("Success:", info.get("success", False))

env.close()
renderer.close()
```

## Run the demo script

```bash
python tools/demo.py --mode random --level basket_case
```

Helpful flags from the demo:

- `--seed 0` to control level variation
- `--max-trials 5` to shorten random demo runs
- `--record-video --video-format mp4` for headless recording
