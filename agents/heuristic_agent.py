"""
Heuristic agent implementation for Interphyre.

This module provides a heuristic agent that uses basic physics knowledge
to make better decisions than random placement.
"""

import numpy as np
from typing import Any, Dict, Optional


class HeuristicAgent:
    """
    A heuristic agent that uses basic physics knowledge.

    This agent analyzes the level and makes informed decisions about
    where to place action objects based on simple heuristics.
    """

    def __init__(self, name: str = "heuristic_agent", seed: Optional[int] = None):
        """
        Initialize the heuristic agent.

        Args:
            name: Name of the agent
            seed: Random seed for reproducibility
        """
        self.name = name
        self.rng = np.random.default_rng(seed)

        # Action space bounds (x, y, size)
        self.x_bounds = (-4.5, 4.5)
        self.y_bounds = (-2.0, 4.0)
        self.size_bounds = (0.4, 0.8)

    def act(self, observation: Any) -> np.ndarray:
        """
        Choose an action based on heuristics.

        Args:
            observation: Current observation from the environment

        Returns:
            Action as a numpy array of shape (3,) for (x, y, size)
        """
        # Extract object information from observation
        objects = observation.get("objects", {})

        # For down_to_earth level, we want to push the green ball off the platform
        # Strategy: place red ball above and to the side of the green ball

        green_ball_pos = None
        red_ball_pos = None
        platform_info = None

        # Find key objects
        for name, obj_data in objects.items():
            if "green" in name.lower():
                green_ball_pos = obj_data.get("position", [0, 0])
            elif "red" in name.lower():
                red_ball_pos = obj_data.get("position", [0, 0])
            elif "platform" in name.lower() or "high" in name.lower():
                platform_info = obj_data

        if green_ball_pos is not None:
            # Strategy 1: Place red ball above and slightly to the side of green ball
            gx, gy = green_ball_pos

            # Place red ball above the green ball
            rx = gx + self.rng.uniform(-1.0, 1.0)  # Slight horizontal offset
            ry = gy + self.rng.uniform(0.5, 1.5)  # Above the green ball

            # Clamp to bounds
            rx = np.clip(rx, self.x_bounds[0], self.x_bounds[1])
            ry = np.clip(ry, self.y_bounds[0], self.y_bounds[1])

            # Choose a reasonable size
            size = self.rng.uniform(0.5, 0.7)

            return np.array([rx, ry, size], dtype=np.float32)

        # Fallback to random if we can't find the green ball
        x = self.rng.uniform(self.x_bounds[0], self.x_bounds[1])
        y = self.rng.uniform(self.y_bounds[0], self.y_bounds[1])
        size = self.rng.uniform(self.size_bounds[0], self.size_bounds[1])

        return np.array([x, y, size], dtype=np.float32)

    def reset(self):
        """Reset the agent's internal state."""
        pass
