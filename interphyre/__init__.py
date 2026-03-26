"""Interphyre - Physics-based puzzle environment for reinforcement learning.

Example usage:
    from interphyre import InterphyreEnv

    env = InterphyreEnv("catapult", seed=42, render_mode="human")
    obs, info = env.reset()
    obs, reward, term, trunc, info = env.step([(0.5, 3.0, 0.6)])
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("interphyre")
except PackageNotFoundError:
    __version__ = "unknown"

from interphyre.environment import InterphyreEnv, InterventionContext
from interphyre.level import Level
from interphyre.config import SimulationConfig
from interphyre.levels import build_level_from_scene, list_levels

__all__ = [
    "InterphyreEnv",
    "InterventionContext",
    "Level",
    "SimulationConfig",
    "build_level_from_scene",
    "list_levels",
    "__version__",
]
