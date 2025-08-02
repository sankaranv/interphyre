"""
Clean DQN agent implementation for Interphyre.

This module provides a DQN agent that uses ONLY the state information
without any domain knowledge or reward shaping.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from typing import Any, Dict, Optional, List, Tuple
from collections import deque
import random


class DQNNetwork(nn.Module):
    """
    Neural network for clean DQN agent.

    Takes observation as input and outputs continuous actions directly.
    """

    def __init__(self, input_size: int, output_size: int, hidden_size: int = 128):
        """
        Initialize the clean DQN network.

        Args:
            input_size: Size of the observation vector
            output_size: Number of action dimensions (3 for x, y, size)
            hidden_size: Size of hidden layers
        """
        super(DQNNetwork, self).__init__()

        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, hidden_size)
        self.fc4 = nn.Linear(hidden_size, output_size)

        # Action bounds for tanh activation
        self.action_bounds = {"x": (-4.5, 4.5), "y": (-2.0, 4.0), "size": (0.4, 0.8)}

    def forward(self, x):
        """Forward pass through the network."""
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        x = torch.tanh(self.fc4(x))  # Output in [-1, 1]
        return x

    def get_action(self, x):
        """Get action in the proper range."""
        raw_action = self.forward(x)

        # Scale to action bounds
        x_scaled = (raw_action[:, 0] + 1) / 2 * (
            self.action_bounds["x"][1] - self.action_bounds["x"][0]
        ) + self.action_bounds["x"][0]
        y_scaled = (raw_action[:, 1] + 1) / 2 * (
            self.action_bounds["y"][1] - self.action_bounds["y"][0]
        ) + self.action_bounds["y"][0]
        size_scaled = (raw_action[:, 2] + 1) / 2 * (
            self.action_bounds["size"][1] - self.action_bounds["size"][0]
        ) + self.action_bounds["size"][0]

        return torch.stack([x_scaled, y_scaled, size_scaled], dim=1)


class DQNAgent:
    """
    Clean DQN agent for Interphyre.

    This agent uses ONLY state information without any domain knowledge
    or reward shaping. Pure reinforcement learning from state transitions.
    """

    def __init__(
        self,
        name: str = "clean_dqn_agent",
        seed: Optional[int] = None,
        learning_rate: float = 1e-3,
        gamma: float = 0.99,
        epsilon: float = 1.0,
        epsilon_min: float = 0.01,
        epsilon_decay: float = 0.995,
        memory_size: int = 10000,
        batch_size: int = 32,
        target_update: int = 100,
        hidden_size: int = 128,
        noise_std: float = 0.1,
    ):
        """
        Initialize the clean DQN agent.

        Args:
            name: Name of the agent
            seed: Random seed for reproducibility
            learning_rate: Learning rate for the optimizer
            gamma: Discount factor for future rewards
            epsilon: Initial exploration rate
            epsilon_min: Minimum exploration rate
            epsilon_decay: Decay rate for epsilon
            memory_size: Size of experience replay buffer
            batch_size: Batch size for training
            target_update: Frequency of target network updates
            hidden_size: Size of hidden layers in the network
            noise_std: Standard deviation of exploration noise
        """
        self.name = name
        self.seed = seed
        if seed is not None:
            torch.manual_seed(seed)
            np.random.seed(seed)
            random.seed(seed)

        # Hyperparameters
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.memory_size = memory_size
        self.batch_size = batch_size
        self.target_update = target_update
        self.hidden_size = hidden_size
        self.noise_std = noise_std

        # Networks will be initialized when we first see an observation
        self.q_network = None
        self.target_network = None
        self.optimizer = None

        # Experience replay buffer
        self.memory = deque(maxlen=memory_size)

        # Training state
        self.step_count = 0
        self.training = True

    def _initialize_networks(self, observation: Any):
        """Initialize networks when we first see an observation."""
        if self.q_network is not None:
            return

        # Convert observation to feature vector
        input_size = self._observation_to_features(observation).shape[0]
        output_size = 3  # x, y, size

        # Create networks
        self.q_network = DQNNetwork(input_size, output_size, self.hidden_size)
        self.target_network = DQNNetwork(input_size, output_size, self.hidden_size)
        self.target_network.load_state_dict(self.q_network.state_dict())

        # Create optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=self.learning_rate)

        print(f"Initialized Clean DQN networks with {input_size} input features")

    def _observation_to_features(self, observation: Any) -> np.ndarray:
        """
        Convert observation to feature vector.

        This function extracts ALL available state information without
        any domain knowledge or object identification.

        Args:
            observation: Environment observation

        Returns:
            Feature vector as numpy array
        """
        features = []

        # Extract object information - NO domain knowledge
        objects = observation.get("objects", {})

        # Add ALL object features without identifying specific objects
        for name, obj_data in objects.items():
            # Add position and velocity for all objects
            pos = obj_data.get("position", [0, 0])
            vel = obj_data.get("velocity", [0, 0])
            features.extend(pos + vel)

            # Add angle and angular velocity
            angle = obj_data.get("angle", 0.0)
            ang_vel = obj_data.get("angular_velocity", 0.0)
            features.extend([angle, ang_vel])

        # Add contact information
        contacts = observation.get("contacts", np.zeros((len(objects), len(objects))))
        features.extend(contacts.flatten())

        # Add step count
        features.append(observation.get("step_count", 0))

        return np.array(features, dtype=np.float32)

    def act(self, observation: Any) -> np.ndarray:
        """
        Choose an action using epsilon-greedy policy with noise.

        Args:
            observation: Current observation

        Returns:
            Action as numpy array [x, y, size]
        """
        # Initialize networks if needed
        self._initialize_networks(observation)

        # Epsilon-greedy action selection
        if self.training and random.random() < self.epsilon:
            # Random action
            x = random.uniform(-4.5, 4.5)
            y = random.uniform(-2.0, 4.0)
            size = random.uniform(0.4, 0.8)
            action = np.array([x, y, size], dtype=np.float32)
        else:
            # Greedy action
            features = self._observation_to_features(observation)
            features_tensor = torch.FloatTensor(features).unsqueeze(0)

            with torch.no_grad():
                action = self.q_network.get_action(features_tensor).squeeze().numpy()

            # Add exploration noise
            if self.training:
                noise = np.random.normal(0, self.noise_std, 3)
                action += noise

                # Clamp to bounds
                action[0] = np.clip(action[0], -4.5, 4.5)
                action[1] = np.clip(action[1], -2.0, 4.0)
                action[2] = np.clip(action[2], 0.4, 0.8)

        return action.astype(np.float32)

    def update(
        self,
        observation: Any,
        action: Any,
        reward: float,
        next_observation: Any,
        terminated: bool,
        truncated: bool,
        info: Dict[str, Any],
    ):
        """
        Update the agent based on experience.

        Uses ONLY the provided reward - no reward shaping or domain knowledge.

        Args:
            observation: Observation before action
            action: Action taken
            reward: Reward received (from environment only)
            next_observation: Observation after action
            terminated: Whether episode terminated due to success
            truncated: Whether episode was truncated
            info: Additional information
        """
        if not self.training:
            return

        # Store experience in replay buffer - use environment reward directly
        self.memory.append(
            (
                self._observation_to_features(observation),
                action,
                reward,  # Use environment reward as-is
                self._observation_to_features(next_observation),
                terminated,
            )
        )

        # Train if we have enough samples
        if len(self.memory) >= self.batch_size:
            self._train()

        # Update target network periodically
        if self.step_count % self.target_update == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())

        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        self.step_count += 1

    def _train(self):
        """Train the Q-network using experience replay."""
        # Sample batch from memory
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        # Convert to tensors
        states = torch.FloatTensor(np.array(states))
        actions = torch.FloatTensor(np.array(actions))
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(np.array(next_states))
        dones = torch.BoolTensor(dones)

        # Current Q-values (using actions as targets)
        current_q_values = self.q_network(states)
        current_q_values = torch.sum(current_q_values * actions, dim=1)

        # Next Q-values (using target network)
        with torch.no_grad():
            next_q_values = self.target_network.get_action(next_states)
            next_q_values = torch.sum(next_q_values * actions, dim=1)
            target_q_values = rewards + (self.gamma * next_q_values * ~dones)

        # Compute loss and update
        loss = F.mse_loss(current_q_values, target_q_values)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def reset(self):
        """Reset the agent's internal state for a new episode."""
        # Keep networks and memory, just reset episode-specific state
        pass

    def set_training(self, training: bool):
        """Set whether the agent is in training mode."""
        self.training = training
        if not training:
            self.epsilon = 0.0  # No exploration during evaluation

    def save(self, path: str):
        """Save the agent's parameters."""
        if self.q_network is not None:
            torch.save(
                {
                    "q_network_state_dict": self.q_network.state_dict(),
                    "target_network_state_dict": self.target_network.state_dict(),
                    "optimizer_state_dict": self.optimizer.state_dict(),
                    "epsilon": self.epsilon,
                    "step_count": self.step_count,
                    "memory": list(self.memory),
                },
                path,
            )

    def load(self, path: str):
        """Load the agent's parameters."""
        if torch.cuda.is_available():
            checkpoint = torch.load(path)
        else:
            checkpoint = torch.load(path, map_location="cpu")

        if self.q_network is not None:
            self.q_network.load_state_dict(checkpoint["q_network_state_dict"])
            self.target_network.load_state_dict(checkpoint["target_network_state_dict"])
            self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            self.epsilon = checkpoint["epsilon"]
            self.step_count = checkpoint["step_count"]
            self.memory = deque(checkpoint["memory"], maxlen=self.memory_size)
