import numpy as np
from typing import Any, Dict, Tuple, Optional
import gymnasium as gym


class RandomAgent:
    """
    Random agent that samples actions uniformly from the environment's action space.
    Used for establishing baseline performance metrics.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the random agent.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.rng = np.random.default_rng(seed)
        self.action_space = None
        
    def set_action_space(self, action_space: gym.Space):
        """
        Set the action space for the agent.
        
        Args:
            action_space: Gymnasium action space
        """
        self.action_space = action_space
        
    def get_action(self, observation: Any) -> np.ndarray:
        """
        Sample a random action from the action space.
        
        Args:
            observation: Current environment observation (not used by random agent)
            
        Returns:
            Random action as numpy array
        """
        if self.action_space is None:
            raise ValueError("Action space not set. Call set_action_space() first.")
            
        return self.action_space.sample()
    
    def reset(self):
        """Reset the agent state (no-op for random agent)."""
        pass
