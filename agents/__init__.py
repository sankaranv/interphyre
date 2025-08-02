"""
Agent training module for Interphyre.

This module provides standardized interfaces and implementations for training
agents to solve physics-based puzzle levels.
"""

from .random_agent import RandomAgent
from .heuristic_agent import HeuristicAgent
from .ppo_agent import PPOAgent
from .dqn_agent import DQNAgent

__all__ = [
    "RandomAgent",
    "HeuristicAgent",
    "DQNAgent",
    "PPOAgent",
]
