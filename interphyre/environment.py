from typing import Optional, Tuple, List, Union, Dict, Any
import gymnasium as gym
import numpy as np

from interphyre.engine import Box2DEngine
from interphyre.level import Level
from interphyre.render import Renderer
from interphyre.config import SimulationConfig


class PhyreEnv(gym.Env):
    """
    A Gymnasium-compatible environment for physics-based puzzle solving.

    This environment provides a physics simulation with configurable objects,
    action spaces for object placement, and observation spaces for state representation.

    Attributes:
        metadata: Environment metadata including render modes and FPS
        action_space: Gymnasium space defining valid actions
        observation_space: Gymnasium space defining valid observations
    """

    metadata = {
        "render_modes": ["human", "rgb_array", "single_rgb_array"],
        "render_fps": 30,
        "name": "PhyreEnv",
    }

    def __init__(
        self,
        level: Level,
        renderer: Optional[Renderer] = None,
        config: Optional[SimulationConfig] = None,
        observation_type: str = "physics_state",
        action_type: str = "continuous",
    ):
        """
        Initialize the Phyre environment.

        Args:
            level: The level configuration containing objects and success conditions
            renderer: Optional renderer for visualization
            config: Optional simulation configuration
            observation_type: Type of observation space ("physics_state", "image", "both")
            action_type: Type of action space ("continuous", "discrete")
        """
        super().__init__()

        if not isinstance(level, Level):
            raise ValueError(f"level must be a Level instance, got {type(level)}")

        self.level = level
        self.renderer = renderer
        self.config = config or SimulationConfig()
        self.observation_type = observation_type
        self.action_type = action_type

        # Initialize engine
        self.engine = Box2DEngine(config=self.config)
        self.action_placed = False
        self.current_obs = None
        self.current_state = None
        self.step_count = 0
        self.max_steps = 1000

        # Set up action space
        self._setup_action_space()

        # Set up observation space
        self._setup_observation_space()

        # Initialize state
        self.reset()

    def _setup_action_space(self):
        """Set up the action space based on action_type and level configuration."""
        if self.action_type == "continuous":
            if len(self.level.action_objects) == 0:
                self.action_space = gym.spaces.Box(
                    low=np.array([]), high=np.array([]), dtype=np.float32
                )
            else:
                # Each action object gets (x, y, size)
                action_dim = len(self.level.action_objects) * 3
                lows = np.array(
                    [-10.0, -10.0, 0.1] * len(self.level.action_objects),
                    dtype=np.float32,
                )
                highs = np.array(
                    [10.0, 10.0, 1.5] * len(self.level.action_objects), dtype=np.float32
                )
                self.action_space = gym.spaces.Box(
                    low=lows, high=highs, shape=(action_dim,), dtype=np.float32
                )
        elif self.action_type == "discrete":
            raise NotImplementedError("Discrete action space not yet implemented")
        else:
            raise ValueError(f"Unknown action_type: {self.action_type}")

    def _setup_observation_space(self):
        """Set up the observation space based on observation_type."""
        if self.observation_type == "physics_state":
            # Physics state observation (object positions, velocities, etc.)
            self.observation_space = gym.spaces.Dict(
                {
                    "objects": gym.spaces.Dict(
                        {
                            name: gym.spaces.Dict(
                                {
                                    "position": gym.spaces.Box(
                                        low=-10, high=10, shape=(2,), dtype=np.float32
                                    ),
                                    "velocity": gym.spaces.Box(
                                        low=-10, high=10, shape=(2,), dtype=np.float32
                                    ),
                                    "angle": gym.spaces.Box(
                                        low=-np.pi,
                                        high=np.pi,
                                        shape=(),
                                        dtype=np.float32,
                                    ),
                                    "angular_velocity": gym.spaces.Box(
                                        low=-10, high=10, shape=(), dtype=np.float32
                                    ),
                                    "type": gym.spaces.Text(max_length=20),
                                }
                            )
                            for name in self.level.objects.keys()
                        }
                    ),
                    "contacts": gym.spaces.Box(
                        low=0,
                        high=1,
                        shape=(len(self.level.objects), len(self.level.objects)),
                        dtype=np.int8,
                    ),
                    "step_count": gym.spaces.Discrete(self.max_steps + 1),
                }
            )
        elif self.observation_type == "image":
            # Image observation (rendered scene)
            self.observation_space = gym.spaces.Box(
                low=0, high=255, shape=(600, 600, 3), dtype=np.uint8
            )
        elif self.observation_type == "both":
            # Both physics state and image
            self.observation_space = gym.spaces.Dict(
                {
                    "physics_state": gym.spaces.Dict(
                        {
                            "objects": gym.spaces.Dict(
                                {
                                    name: gym.spaces.Dict(
                                        {
                                            "position": gym.spaces.Box(
                                                low=-10,
                                                high=10,
                                                shape=(2,),
                                                dtype=np.float32,
                                            ),
                                            "velocity": gym.spaces.Box(
                                                low=-10,
                                                high=10,
                                                shape=(2,),
                                                dtype=np.float32,
                                            ),
                                            "angle": gym.spaces.Box(
                                                low=-np.pi,
                                                high=np.pi,
                                                shape=(),
                                                dtype=np.float32,
                                            ),
                                            "angular_velocity": gym.spaces.Box(
                                                low=-10,
                                                high=10,
                                                shape=(),
                                                dtype=np.float32,
                                            ),
                                            "type": gym.spaces.Text(max_length=20),
                                        }
                                    )
                                    for name in self.level.objects.keys()
                                }
                            ),
                            "contacts": gym.spaces.Box(
                                low=0,
                                high=1,
                                shape=(
                                    len(self.level.objects),
                                    len(self.level.objects),
                                ),
                                dtype=np.int8,
                            ),
                            "step_count": gym.spaces.Discrete(self.max_steps + 1),
                        }
                    ),
                    "image": gym.spaces.Box(
                        low=0, high=255, shape=(600, 600, 3), dtype=np.uint8
                    ),
                }
            )
        else:
            raise ValueError(f"Unknown observation_type: {self.observation_type}")

    def reset(
        self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Reset the environment to initial state.

        Args:
            seed: Random seed for reproducibility
            options: Additional options for reset

        Returns:
            Tuple of (observation, info)
        """
        super().reset(seed=seed)

        # Reset engine and state
        self.engine.reset(self.level)
        self.action_placed = False
        self.step_count = 0

        # Get initial observation
        observation = self._get_observation()

        # Prepare info dictionary
        info = {
            "level_name": self.level.name,
            "action_objects": self.level.action_objects,
            "total_objects": len(self.level.objects),
            "step_count": self.step_count,
            "action_placed": self.action_placed,
            "success": False,
            "truncated": False,
        }

        return observation, info

    def step(
        self, action: Union[List[Tuple[float, float, float]], np.ndarray]
    ) -> Tuple[Any, float, bool, bool, Dict[str, Any]]:
        """
        Take a step in the environment.

        Args:
            action: Action to take. For continuous actions, should be a list of (x, y, size) tuples
                   or a numpy array of shape (n_objects * 3,)

        Returns:
            Tuple of (observation, reward, terminated, truncated, info)
        """
        # Validate and convert action
        converted_action = self._validate_action(action)

        # Place action objects if not already placed
        if not self.action_placed:
            self._place_action_objects(converted_action)
            self.action_placed = True

        # Simulate one step
        self.engine.world.Step(
            self.config.time_step,
            self.config.velocity_iters,
            self.config.position_iters,
        )
        self.engine.time_update(self.config.time_step)

        # Update step count
        self.step_count += 1

        # Check termination conditions
        success = self.level.success_condition(self.engine)
        terminated = success
        truncated = self.step_count >= self.max_steps

        # Calculate reward
        reward = self._calculate_reward(success, truncated)

        # Get observation
        observation = self._get_observation()

        # Prepare info dictionary
        info = self._get_info_dict(success, terminated, truncated)

        return observation, reward, terminated, truncated, info

    def _validate_action(
        self, action: Union[List[Tuple[float, float, float]], np.ndarray]
    ) -> List[Tuple[float, float, float]]:
        """Validate the action format and values (x, y, size for each object)."""
        if len(self.level.action_objects) == 0:
            if action != [] and not (
                isinstance(action, np.ndarray) and action.size == 0
            ):
                raise ValueError(
                    f"No action objects in level, but received action: {action}"
                )
            return []

        expected_dim = len(self.level.action_objects) * 3

        if isinstance(action, np.ndarray):
            if action.shape != (expected_dim,):
                raise ValueError(
                    f"Expected action shape ({expected_dim},), got {action.shape}"
                )
            # Convert to list of tuples for processing
            converted_action = [
                (action[i], action[i + 1], np.clip(action[i + 2], 0.1, 1.5))
                for i in range(0, len(action), 3)
            ]
        elif isinstance(action, list):
            if len(action) != len(self.level.action_objects):
                raise ValueError(
                    f"Expected {len(self.level.action_objects)} action tuples, got {len(action)}"
                )
            for i, pos in enumerate(action):
                if not isinstance(pos, (tuple, list)) or len(pos) != 3:
                    raise ValueError(
                        f"Action {i} must be a tuple/list of length 3 (x, y, size), got {pos}"
                    )
                if not all(isinstance(x, (int, float)) for x in pos):
                    raise ValueError(
                        f"Action {i} coordinates must be numbers, got {pos}"
                    )
            # Clamp size
            converted_action = [(x, y, np.clip(s, 0.1, 2.0)) for (x, y, s) in action]
        else:
            raise ValueError(
                f"Action must be list of tuples or numpy array, got {type(action)}"
            )

        return converted_action

    def _place_action_objects(self, action: List[Tuple[float, float, float]]):
        """Place action objects at the specified positions and sizes."""
        if len(action) != len(self.level.action_objects):
            raise ValueError(
                f"Expected {len(self.level.action_objects)} positions, got {len(action)}"
            )
        self.engine.place_action_objects(action)

    def _get_observation(self) -> Any:
        """Get the current observation based on observation_type."""
        if self.observation_type == "physics_state":
            return self._get_physics_state()
        elif self.observation_type == "image":
            return self._get_image_observation()
        elif self.observation_type == "both":
            return {
                "physics_state": self._get_physics_state(),
                "image": self._get_image_observation(),
            }
        else:
            raise ValueError(f"Unknown observation_type: {self.observation_type}")

    def _get_physics_state(self) -> Dict[str, Any]:
        """Get the physics state observation."""
        if self.engine.world is None:
            return {}

        # Get object states
        objects_state = {}
        object_names = list(self.level.objects.keys())

        for name in object_names:
            if name in self.engine.bodies:
                body = self.engine.bodies[name]
                objects_state[name] = {
                    "position": np.array(
                        [body.position.x, body.position.y], dtype=np.float32
                    ),
                    "velocity": np.array(
                        [body.linearVelocity.x, body.linearVelocity.y], dtype=np.float32
                    ),
                    "angle": float(body.angle),
                    "angular_velocity": float(body.angularVelocity),
                    "type": type(self.level.objects[name]).__name__,
                }
            else:
                # Object not yet placed (e.g., action objects)
                obj = self.level.objects[name]
                objects_state[name] = {
                    "position": np.array([obj.x, obj.y], dtype=np.float32),
                    "velocity": np.array([0.0, 0.0], dtype=np.float32),
                    "angle": float(obj.angle),
                    "angular_velocity": 0.0,
                    "type": type(obj).__name__,
                }

        # Get contact matrix
        contact_matrix = np.zeros(
            (len(object_names), len(object_names)), dtype=np.bool_
        )
        for i, name1 in enumerate(object_names):
            for j, name2 in enumerate(object_names):
                if i != j and self.engine.has_contact(name1, name2):
                    contact_matrix[i, j] = True

        return {
            "objects": objects_state,
            "contacts": contact_matrix,
            "step_count": self.step_count,
        }

    def _get_image_observation(self) -> np.ndarray:
        """Get the image observation (placeholder for now)."""
        # This would render the scene to an image
        # For now, return a placeholder
        return np.zeros((600, 600, 3), dtype=np.uint8)

    def _calculate_reward(self, success: bool, truncated: bool) -> float:
        """Calculate the reward for the current state."""
        if success:
            return 1.0
        elif truncated:
            return -0.1  # Small penalty for timeout
        else:
            return 0.0  # No reward for intermediate steps

    def _get_info_dict(
        self, success: bool, terminated: bool, truncated: bool
    ) -> Dict[str, Any]:
        """Get the info dictionary for the current step."""
        info = {
            "level_name": self.level.name,
            "step_count": self.step_count,
            "action_placed": self.action_placed,
            "success": success,
            "terminated": terminated,
            "truncated": truncated,
            "world_stationary": (
                self.engine.world_is_stationary() if self.engine.world else False
            ),
        }

        # Add contact statistics if available
        if hasattr(self.engine, "get_contact_statistics"):
            contact_stats = self.engine.get_contact_statistics()
            info["contact_statistics"] = contact_stats

        # Add performance statistics if profiling is enabled
        if self.config.enable_profiling:
            perf_stats = self.engine.profiler.get_stats()
            info["performance_stats"] = perf_stats

        return info

    def simulate(
        self,
        steps: int = 1000,
        return_trace: bool = False,
        verbose: bool = False,
    ) -> Optional[List[Tuple[Any, float, bool, bool, Dict[str, Any]]]]:
        """
        Simulate multiple steps and optionally return a trace.

        Args:
            steps: Maximum number of steps to simulate
            return_trace: Whether to return the full trace
            verbose: Whether to print progress

        Returns:
            List of (observation, reward, terminated, truncated, info) tuples if return_trace=True,
            otherwise None
        """
        if self.engine.world is None:
            raise ValueError(
                "World is not initialized. Call reset() before simulating."
            )

        trace = []
        status = "running"
        terminated = False

        # Use batch profiling for efficiency during long simulations
        if self.config.enable_profiling:
            self.engine.profiler.start_step_batch()

        for i in range(steps):
            self.engine.world.Step(
                self.config.time_step,
                self.config.velocity_iters,
                self.config.position_iters,
            )
            self.engine.time_update(self.config.time_step)

            done = self.level.success_condition(self.engine)
            if done:
                status = "success"
            elif self.engine.world_is_stationary():
                status = "world_is_stationary"
            elif i == steps - 1:
                status = "timeout"
                terminated = True

            if return_trace:
                observation = self._get_observation()
                reward = self._calculate_reward(done, terminated)
                info = self._get_info_dict(done, done, terminated)
                trace.append((observation, reward, done, terminated, info))

            # Render the current state if a renderer is provided
            self.render()

            if verbose:
                print(f"Step {i+1}/{steps}, status: {status}")
            if done or terminated:
                break

        # End batch profiling
        if self.config.enable_profiling:
            self.engine.profiler.end_step_batch(steps)

        return trace if return_trace else None

    def render(self):
        """Render the current state."""
        if self.renderer:
            self.renderer.render(self.engine)

    def close(self):
        """Close the environment and clean up resources."""
        if self.renderer:
            self.renderer.close()

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics from the engine's profiler."""
        return self.engine.profiler.get_stats()

    def reset_profiler(self):
        """Reset the performance profiler."""
        self.engine.profiler.reset()

    def get_contact_log(self) -> List[Dict[str, Any]]:
        """Get the full contact event log for research purposes."""
        return self.engine.get_contact_log()

    def get_contact_statistics(self) -> Dict[str, Any]:
        """Get statistics about all contacts for research purposes."""
        return self.engine.get_contact_statistics()

    def get_level_info(self) -> Dict[str, Any]:
        """Get information about the current level."""
        return {
            "name": self.level.name,
            "action_objects": self.level.action_objects,
            "total_objects": len(self.level.objects),
            "object_types": {
                name: type(obj).__name__ for name, obj in self.level.objects.items()
            },
            "metadata": self.level.metadata,
        }
