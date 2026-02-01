# Interphyre

Physics-based puzzle environment for reinforcement learning and causal inference research.

## Features

- **25+ Procedurally Generated Levels** - Diverse physics puzzles with configurable difficulty
- **Gymnasium-Compatible API** - Standard RL interface for training agents
- **Intervention System** - Multi-turn control and counterfactual reasoning capabilities
- **Deterministic Physics** - Reproducible simulations using Box2D
- **Multiple Rendering Backends** - Pygame for visualization, OpenCV for headless operation
- **Custom Level Creation** - Build your own puzzles with a simple API
- **Comprehensive Documentation** - Examples, tutorials, and API reference

## Installation

```bash
git clone https://github.com/sankaranv/interphyre
cd interphyre
pip install -e .
```

## Quick Start

```python
from interphyre import InterphyreEnv

# Create environment
env = InterphyreEnv("catapult", seed=42)

# Reset and take an action
obs, info = env.reset()
obs, reward, terminated, truncated, info = env.step((0.5, 3.0, 0.6))

print(f"Success: {info['success']}")
env.close()
```

## Visualization

```bash
# View a level interactively
python -m interphyre.viewer catapult --seed 42 --action 0.5 3.0 0.6

# Run random demo
python -m interphyre.viewer --demo catapult --trials 10
```

## Documentation

Full documentation is available at [https://sankaranv.github.io/interphyre](https://sankaranv.github.io/interphyre)

## Level Gallery

Interphyre includes 25 physics puzzle levels across varying difficulty:

**One-Ball Levels:** basket_case, catapult, dive_bomb, flagpole_sitta, just_a_nudge, locust_swarm, mind_the_gap, off_the_rails, pass_the_parcel, pinball_machine, seesaw, the_cradle, tipping_point, two_body_problem

**Two-Ball Levels:** Additional levels with multiple dynamic balls

## Research Applications

- **Reinforcement Learning** - Train agents to solve physics puzzles
- **Causal Inference** - Intervention-based reasoning and counterfactuals
- **Transfer Learning** - Cross-level generalization
- **Model-Based Planning** - Physics-aware decision making

## License

[MIT](LICENSE)

## Citation

If you use Interphyre in your research, please cite:

```bibtex
@software{interphyre2026,
  title={Interphyre: Physics-based Puzzle Environment for RL and Causal Inference},
  author={Vaidyanathan, Sankaran},
  year={2026},
  url={https://github.com/sankaranv/interphyre}
}
```
