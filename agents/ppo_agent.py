"""
PPO (Proximal Policy Optimization) agent implementation for Interphyre.

This module provides a PPO agent that uses ONLY the state information
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


class PPONetwork(nn.Module):
    """
    Neural network for PPO agent.

    Takes observation as input and outputs action distribution parameters.
    """

    def __init__(self, input_size: int, action_size: int, hidden_size: int = 128):
        """
        Initialize the PPO network.

        Args:
            input_size: Size of the observation vector
            action_size: Number of action dimensions (3 for x, y, size)
            hidden_size: Size of hidden layers
        """
        super(PPONetwork, self).__init__()

        # Shared feature extractor
        self.feature_net = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
        )

        # Policy head (actor)
        self.policy_mean = nn.Linear(hidden_size, action_size)
        self.policy_logstd = nn.Parameter(torch.zeros(action_size))

        # Value head (critic)
        self.value_head = nn.Linear(hidden_size, 1)

        # Action bounds
        self.action_bounds = {"x": (-4.5, 4.5), "y": (-4.5, 4.5), "size": (0.4, 0.8)}

    def forward(self, x):
        """Forward pass through the network."""
        features = self.feature_net(x)

        # Policy outputs
        action_mean = self.policy_mean(features)
        action_logstd = self.policy_logstd.expand_as(action_mean)

        # Value output
        value = self.value_head(features)

        return action_mean, action_logstd, value

    def get_action(self, x, deterministic=False):
        """Get action from the policy."""
        action_mean, action_logstd, value = self.forward(x)

        if deterministic:
            action = action_mean
        else:
            # Sample from normal distribution
            action_std = torch.exp(action_logstd)
            normal = torch.distributions.Normal(action_mean, action_std)
            action = normal.sample()

        # Scale to action bounds
        x_scaled = (
            torch.tanh(action[:, 0])
            * (self.action_bounds["x"][1] - self.action_bounds["x"][0])
            / 2
            + (self.action_bounds["x"][1] + self.action_bounds["x"][0]) / 2
        )
        y_scaled = (
            torch.tanh(action[:, 1])
            * (self.action_bounds["y"][1] - self.action_bounds["y"][0])
            / 2
            + (self.action_bounds["y"][1] + self.action_bounds["y"][0]) / 2
        )
        size_scaled = (
            torch.sigmoid(action[:, 2])
            * (self.action_bounds["size"][1] - self.action_bounds["size"][0])
            + self.action_bounds["size"][0]
        )

        return torch.stack([x_scaled, y_scaled, size_scaled], dim=1), value

    def evaluate_actions(self, x, actions):
        """Evaluate actions for PPO loss calculation."""
        action_mean, action_logstd, value = self.forward(x)
        action_std = torch.exp(action_logstd)
        normal = torch.distributions.Normal(action_mean, action_std)

        # Calculate log probability of actions
        log_prob = normal.log_prob(actions).sum(dim=-1)
        entropy = normal.entropy().sum(dim=-1)

        return log_prob, entropy, value


class PPOBuffer:
    """Buffer for storing PPO experiences."""

    def __init__(self, buffer_size: int):
        self.buffer_size = buffer_size
        self.reset()

    def reset(self):
        """Reset the buffer."""
        self.states = []
        self.actions = []
        self.rewards = []
        self.values = []
        self.log_probs = []
        self.dones = []

    def add(self, state, action, reward, value, log_prob, done):
        """Add experience to buffer."""
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.values.append(value)
        self.log_probs.append(log_prob)
        self.dones.append(done)

    def get_batch(self):
        """Get all experiences as tensors."""
        states = torch.FloatTensor(np.array(self.states))
        actions = torch.FloatTensor(np.array(self.actions))
        rewards = torch.FloatTensor(self.rewards)
        values = torch.FloatTensor(self.values)
        log_probs = torch.FloatTensor(self.log_probs)
        dones = torch.BoolTensor(self.dones)

        return states, actions, rewards, values, log_probs, dones


class PPOAgent:
    """
    PPO (Proximal Policy Optimization) agent for Interphyre.

    This agent uses ONLY state information without any domain knowledge
    or reward shaping. Pure reinforcement learning from state transitions.
    """

    def __init__(
        self,
        name: str = "ppo_agent",
        seed: Optional[int] = None,
        learning_rate: float = 3e-4,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_ratio: float = 0.2,
        value_loss_coef: float = 0.5,
        entropy_coef: float = 0.01,
        max_grad_norm: float = 0.5,
        hidden_size: int = 128,
        buffer_size: int = 2048,
        batch_size: int = 64,
        epochs_per_update: int = 10,
    ):
        """
        Initialize the PPO agent.

        Args:
            name: Name of the agent
            seed: Random seed for reproducibility
            learning_rate: Learning rate for the optimizer
            gamma: Discount factor for future rewards
            gae_lambda: GAE lambda parameter
            clip_ratio: PPO clip ratio
            value_loss_coef: Value loss coefficient
            entropy_coef: Entropy coefficient for exploration
            max_grad_norm: Maximum gradient norm for clipping
            hidden_size: Size of hidden layers
            buffer_size: Size of experience buffer
            batch_size: Batch size for training
            epochs_per_update: Number of epochs per PPO update
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
        self.gae_lambda = gae_lambda
        self.clip_ratio = clip_ratio
        self.value_loss_coef = value_loss_coef
        self.entropy_coef = entropy_coef
        self.max_grad_norm = max_grad_norm
        self.hidden_size = hidden_size
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        self.epochs_per_update = epochs_per_update

        # Networks will be initialized when we first see an observation
        self.policy = None
        self.optimizer = None

        # Experience buffer
        self.buffer = PPOBuffer(buffer_size)

        # Training state
        self.step_count = 0
        self.training = True

    def _initialize_networks(self, observation: Any):
        """Initialize networks when we first see an observation."""
        if self.policy is not None:
            return

        # Convert observation to feature vector
        input_size = self._observation_to_features(observation).shape[0]
        action_size = 3  # x, y, size

        # Create policy network
        self.policy = PPONetwork(input_size, action_size, self.hidden_size)

        # Create optimizer
        self.optimizer = optim.Adam(self.policy.parameters(), lr=self.learning_rate)

        print(f"Initialized PPO networks with {input_size} input features")

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
        Choose an action using the policy.

        Args:
            observation: Current observation

        Returns:
            Action as numpy array [x, y, size]
        """
        # Initialize networks if needed
        self._initialize_networks(observation)

        # Debug: print observation type and shape
        print(f"[DEBUG] Observation type: {type(observation)}")
        if isinstance(observation, dict):
            print(f"[DEBUG] Observation keys: {list(observation.keys())}")
        else:
            print(f"[DEBUG] Observation: {observation}")

        # Get features
        features = self._observation_to_features(observation)
        print(
            f"[DEBUG] Feature vector shape: {features.shape}, dtype: {features.dtype}"
        )
        features_tensor = torch.FloatTensor(features).unsqueeze(0)

        # Get action from policy
        with torch.no_grad():
            action, value = self.policy.get_action(
                features_tensor, deterministic=not self.training
            )
            action = action.squeeze().numpy()
            value = value.squeeze().item()

        # Store for training
        if self.training:
            # Calculate log probability
            with torch.no_grad():
                log_prob, _, _ = self.policy.evaluate_actions(
                    features_tensor, torch.FloatTensor(action).unsqueeze(0)
                )
                log_prob = log_prob.squeeze().item()

            # Store in buffer
            self.buffer.add(
                features, action, 0.0, value, log_prob, False
            )  # reward and done will be updated later

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

        # Update the last experience in buffer
        if len(self.buffer.rewards) > 0:
            self.buffer.rewards[-1] = reward
            self.buffer.dones[-1] = terminated or truncated

        # Train if buffer is full
        if len(self.buffer.states) >= self.buffer_size:
            self._train()

    def _compute_gae(self, rewards, values, dones):
        """Compute Generalized Advantage Estimation."""
        advantages = np.zeros_like(rewards)
        last_advantage = 0
        last_value = 0

        for t in reversed(range(len(rewards))):
            if t == len(rewards) - 1:
                next_value = 0
            else:
                next_value = values[t + 1]

            delta = rewards[t] + self.gamma * next_value * (1 - dones[t]) - values[t]
            advantages[t] = (
                delta + self.gamma * self.gae_lambda * (1 - dones[t]) * last_advantage
            )
            last_advantage = advantages[t]

        returns = advantages + values
        return advantages, returns

    def _train(self):
        """Train the policy using PPO."""
        # Get batch from buffer
        states, actions, rewards, values, log_probs, dones = self.buffer.get_batch()

        # Compute GAE
        advantages, returns = self._compute_gae(
            rewards.numpy(), values.numpy(), dones.numpy()
        )
        advantages = torch.FloatTensor(advantages)
        returns = torch.FloatTensor(returns)

        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # PPO training
        for epoch in range(self.epochs_per_update):
            # Create mini-batches
            indices = torch.randperm(len(states))

            for start_idx in range(0, len(states), self.batch_size):
                end_idx = start_idx + self.batch_size
                batch_indices = indices[start_idx:end_idx]

                batch_states = states[batch_indices]
                batch_actions = actions[batch_indices]
                batch_advantages = advantages[batch_indices]
                batch_returns = returns[batch_indices]
                batch_old_log_probs = log_probs[batch_indices]

                # Forward pass
                new_log_probs, entropy, new_values = self.policy.evaluate_actions(
                    batch_states, batch_actions
                )

                # Compute ratios
                ratio = torch.exp(new_log_probs - batch_old_log_probs)

                # PPO loss
                surr1 = ratio * batch_advantages
                surr2 = (
                    torch.clamp(ratio, 1 - self.clip_ratio, 1 + self.clip_ratio)
                    * batch_advantages
                )
                policy_loss = -torch.min(surr1, surr2).mean()

                # Value loss
                value_loss = F.mse_loss(new_values.squeeze(), batch_returns)

                # Total loss
                loss = (
                    policy_loss
                    + self.value_loss_coef * value_loss
                    - self.entropy_coef * entropy.mean()
                )

                # Backward pass
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(
                    self.policy.parameters(), self.max_grad_norm
                )
                self.optimizer.step()

        # Reset buffer
        self.buffer.reset()
        self.step_count += 1

    def reset(self):
        """Reset the agent's internal state for a new episode."""
        # Reset buffer for new episode
        self.buffer.reset()

    def set_training(self, training: bool):
        """Set whether the agent is in training mode."""
        self.training = training

    def save(self, path: str):
        """Save the agent's parameters."""
        if self.policy is not None:
            torch.save(
                {
                    "policy_state_dict": self.policy.state_dict(),
                    "optimizer_state_dict": self.optimizer.state_dict(),
                    "step_count": self.step_count,
                },
                path,
            )

    def load(self, path: str):
        """Load the agent's parameters."""
        if torch.cuda.is_available():
            checkpoint = torch.load(path)
        else:
            checkpoint = torch.load(path, map_location="cpu")

        if self.policy is not None:
            self.policy.load_state_dict(checkpoint["policy_state_dict"])
            self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            self.step_count = checkpoint["step_count"]
