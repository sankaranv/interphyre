"""Interphyre - Physics-based puzzle environment for reinforcement learning.

Example usage:
    from interphyre import PhyreEnv

    env = PhyreEnv("catapult", seed=42, render_mode="human")
    obs, info = env.reset()
    obs, reward, term, trunc, info = env.step([(0.5, 3.0, 0.6)])
"""

from interphyre.environment import PhyreEnv, InterventionContext
from interphyre.level import Level
from interphyre.config import SimulationConfig

__all__ = [
    "PhyreEnv",
    "InterventionContext",
    "Level",
    "SimulationConfig",
]
