"""
Random agent implementation for Interphyre.

This module provides a simple random agent that serves as a baseline
for testing the training infrastructure.
"""

import numpy as np
from typing import Any, Dict, List, Tuple, Union, Optional


class RandomAgent:
    """
    A simple random agent that chooses random actions.

    This agent serves as a baseline for testing the training infrastructure.
    """

    def __init__(self, name: str = "random_agent", seed: Optional[int] = None):
        """
        Initialize the random agent.

        Args:
            name: Name of the agent
            seed: Random seed for reproducibility
        """
        self.name = name
        self.rng = np.random.default_rng(seed)

        # Action space bounds (x, y, size)
        self.x_bounds = (-4.5, 4.5)  # Reasonable x range for most levels
        self.y_bounds = (-2.0, 4.0)  # Reasonable y range for most levels
        self.size_bounds = (0.4, 0.8)  # Reasonable size range for balls

    def act(self, observation: Any) -> np.ndarray:
        """
        Choose a random action.

        Args:
            observation: Current observation (not used by random agent)

        Returns:
            Random action as a numpy array of shape (3,) for (x, y, size)
        """
        # Generate random action for a single object (most levels have one action object)
        x = self.rng.uniform(self.x_bounds[0], self.x_bounds[1])
        y = self.rng.uniform(self.y_bounds[0], self.y_bounds[1])
        size = self.rng.uniform(self.size_bounds[0], self.size_bounds[1])

        return np.array([x, y, size], dtype=np.float32)

    def reset(self):
        """Reset the agent's internal state."""
        # Random agent doesn't have internal state to reset
        pass
