# Agent Training for Interphyre

This directory contains the agent training infrastructure for the Interphyre physics puzzle environment.

## Overview

The agent training system allows you to train agents to solve physics-based puzzle levels in Interphyre. The system follows a standard reinforcement learning workflow:

1. **Episode Structure**: Each episode consists of multiple trials
2. **Action**: Agent places action objects (x, y, size) in the environment
3. **Simulation**: Physics simulation runs until success/failure
4. **Repeat**: Process continues until success or max trials reached

## Architecture

### Library vs Agents
- **Interphyre Library** (`interphyre/`): The core physics simulation and environment
- **Agents** (`agents/`): Separate agent implementations that use the library

### Key Components

#### Environment (`interphyre/environment.py`)
- `PhyreEnv`: Gymnasium-compatible environment
- `run_episode()`: Runs complete episode with given action
- Standard gym interface: `reset()`, `step()`, `observation_space`, `action_space`

#### Training Loop (`tools/train_agent.py`)
- `TrainingLoop`: Manages the training process
- Handles episode structure and statistics
- Supports multiple agents and levels

#### Agents
- `RandomAgent`: Baseline random action selection
- `HeuristicAgent`: Uses basic physics knowledge for better decisions

## Usage

### Basic Training

```python
from agents import RandomAgent
from tools.train_agent import TrainingLoop

# Create agent
agent = RandomAgent(name="my_agent", seed=42)

# Create training loop
trainer = TrainingLoop(
    level_name="down_to_earth",
    agent=agent,
    max_trials=50,
    max_steps_per_trial=1000,
    verbose=True
)

# Train
stats = trainer.train(num_episodes=10)
print(f"Success rate: {stats['success_rate']:.2%}")
```

### Agent Comparison

```bash
python tools/compare_agents.py
```

This compares different agents on the same level and shows performance metrics.

### Custom Agents

To create a custom agent, implement the following interface:

```python
class MyAgent:
    def __init__(self, name: str = "my_agent", **kwargs):
        self.name = name
        # Initialize your agent
    
    def act(self, observation: Any) -> np.ndarray:
        """
        Choose an action based on observation.
        
        Args:
            observation: Environment observation
            
        Returns:
            Action as numpy array of shape (3,) for (x, y, size)
        """
        # Your action selection logic
        return np.array([x, y, size], dtype=np.float32)
    
    def reset(self):
        """Reset agent state for new episode."""
        pass
```

## Levels

Currently supported levels:
- `down_to_earth`: Push green ball off platform to ground

## Action Space

Actions are continuous and represent object placement:
- **x**: Horizontal position (-4.5 to 4.5)
- **y**: Vertical position (-2.0 to 4.0)  
- **size**: Object size (0.4 to 0.8)

## Observation Space

The environment provides physics state observations including:
- Object positions and velocities
- Contact information
- Step count

## Performance

Example results on `down_to_earth` level:
- **Random Agent**: 100% success rate, ~6.2 trials per episode
- **Heuristic Agent**: 100% success rate, ~1.0 trials per episode

## Future Work

- Implement learning agents (RL, imitation learning)
- Add more sophisticated heuristics
- Support for more complex levels
- Visualization and debugging tools
- Hyperparameter optimization 