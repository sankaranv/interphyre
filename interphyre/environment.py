from typing import Optional, Tuple, List, Union, Dict, Any
import gymnasium as gym
import numpy as np

from interphyre.engine import Box2DEngine
from interphyre.level import Level
from interphyre.render import Renderer
from interphyre.config import SimulationConfig, PRECISION


class PhyreEnv(gym.Env):
    """

    This environment simulates physics puzzles where agents place objects to achieve
    specific goals. The environment follows a one-shot paradigm: agents provide an
    action (object placement), then the full simulation runs to completion.

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
        image_size: Tuple[int, int] = (600, 600),
        image_ppm: float = 60.0,
        discrete_colors: bool = False,
    ):
        """
        Initialize the Phyre environment.

        Args:
            level: The level configuration containing objects and success conditions
            renderer: Optional renderer for visualization (PygameRenderer recommended)
            config: Optional simulation configuration (uses defaults if None)
            observation_type: Type of observation space ("physics_state", "image", "both")
            action_type: Type of action space ("continuous", "discrete")
            image_size: Size of rendered images (width, height) for image observations
            image_ppm: Pixels per Box2D unit for image rendering
            discrete_colors: If True, use single-channel discrete colors instead of RGB
        """
        super().__init__()

        if not isinstance(level, Level):
            raise ValueError(f"level must be a Level instance, got {type(level)}")

        self.level = level
        self.renderer = renderer
        self.config = config or SimulationConfig()
        self.observation_type = observation_type
        self.action_type = action_type
        self.image_size = image_size
        self.image_ppm = image_ppm
        self.discrete_colors = discrete_colors

        # Initialize engine
        self.engine = Box2DEngine(config=self.config)
        self.action_placed = False
        self.current_obs = None
        self.current_state = None
        self.step_count = 0
        self.max_steps = self.config.max_steps
        self._rollout_complete = False
        self._active_interventions: List[Any] = []

        # Set up action space
        self._setup_action_space()

        # Set up observation space
        self._setup_observation_space()

        # Initialize numpy random generator
        self.np_random = np.random.default_rng()

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
                    [-5.0, -5.0, 0.1] * len(self.level.action_objects),
                    dtype=np.float32,
                )
                highs = np.array(
                    [5.0, 5.0, 1.5] * len(self.level.action_objects), dtype=np.float32
                )
                self.action_space = gym.spaces.Box(
                    low=lows, high=highs, shape=(action_dim,), dtype=np.float32
                )
        elif self.action_type == "discrete":
            # Discretize the same bounds as continuous with step size 0.1
            num_objects = len(self.level.action_objects)
            if num_objects == 0:
                # Empty MultiDiscrete for no-action levels
                self.action_space = gym.spaces.MultiDiscrete(
                    np.array([], dtype=np.int64)
                )
            else:
                # For x and y: [-5.0, 5.0] inclusive with 0.1 step => 101 bins
                # For size: [0.1, 1.5] inclusive with 0.1 step => 15 bins
                # Use integer arithmetic to avoid subtle floating-point rounding issues
                x_y_bins = int((5.0 - (-5.0)) / 0.1 + 1)  # 101
                size_bins = int((1.5 - 0.1) / 0.1 + 1)  # 15

                # Store for validation/mapping
                self._discrete_step = 0.1
                self._discrete_bins = (x_y_bins, x_y_bins, size_bins)
                self._discrete_lows = (-5.0, -5.0, 0.1)

                # Repeat [x_bins, y_bins, size_bins] per action object
                nvec = np.array(list(self._discrete_bins) * num_objects, dtype=np.int64)
                self.action_space = gym.spaces.MultiDiscrete(nvec)
        else:
            raise ValueError(f"Unknown action_type: {self.action_type}")

    def _setup_observation_space(self):
        """Set up the observation space based on observation_type."""
        if self.observation_type == "physics_state":
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
            width, height = self.image_size
            if self.discrete_colors:
                self.observation_space = gym.spaces.Box(
                    low=0, high=7, shape=(height, width), dtype=np.uint8
                )
            else:
                self.observation_space = gym.spaces.Box(
                    low=0, high=255, shape=(height, width, 3), dtype=np.uint8
                )
        elif self.observation_type == "both":
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
                        low=0,
                        high=255 if not self.discrete_colors else 7,
                        shape=(
                            (self.image_size[1], self.image_size[0], 3)
                            if not self.discrete_colors
                            else (self.image_size[1], self.image_size[0])
                        ),
                        dtype=np.uint8,
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
            seed: Random seed for reproducibility (optional)
            options: Additional options for reset (e.g., interventions)

        Returns:
            Tuple of (observation, info) where:
                observation: Initial state observation
                info: Dictionary with level info, object counts, etc.

        Note:
            This method must be called before step() for each new episode.
        """
        super().reset(seed=seed)

        # Set the seed for numpy random generator
        if seed is not None:
            self.np_random = np.random.default_rng(seed)

        # Reset engine and state
        self.engine.reset(self.level)
        self.action_placed = False
        self.step_count = 0
        self._rollout_complete = False

        # Load interventions from options
        self._active_interventions = []
        if options and "interventions" in options:
            self._active_interventions = options["interventions"]

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
            "terminated": False,
        }

        return observation, info

    def step(
        self, action: Union[List[Tuple[float, float, float]], np.ndarray]
    ) -> Tuple[Any, float, bool, bool, Dict[str, Any]]:
        """
        Execute one episode: place objects and run full simulation to completion.

        This is a one-shot environment - step() can only be called once per episode.
        After calling step(), you must call reset() to start a new episode.

        Args:
            action: Action to execute. For continuous actions, should be:
                - List of (x, y, size) tuples for each action object
                - Numpy array of shape (n_objects * 3,) with flattened coordinates

        Returns:
            Tuple of (observation, reward, terminated, truncated, info):
                observation: Final state after simulation completes
                reward: Reward for the episode (1.0 for success, -0.1 for timeout, 0.0 otherwise)
                terminated: Whether success condition was met
                truncated: Whether max steps reached
                info: Dictionary with episode information and statistics

        """
        if self._rollout_complete:
            raise RuntimeError(
                "Episode already complete. Call reset() to start a new episode."
            )

        # Validate action and check for invalid placements
        validation_result = self._validate_action_with_failure(action)
        if validation_result["invalid"]:
            # Return failure reward immediately without running simulation
            obs = self._get_observation()
            info = {
                "level_name": self.level.name,
                "step_count": 0,
                "action_placed": False,
                "success": False,
                "terminated": True,
                "truncated": False,
                "world_stationary": False,
                "validation_error": validation_result["error"],
                "invalid_action": True,
            }
            self._rollout_complete = True
            return obs, -1.0, True, False, info  # Failure reward: -1.0

        # Place action objects (validation passed)
        self._place_action_objects(validation_result["action"])
        self.action_placed = True

        # Run full simulation to completion
        obs, reward, terminated, truncated, info = self._run_simulation_rollout()
        self._rollout_complete = True
        return obs, reward, terminated, truncated, info

    def _step_physics(self):
        """
        Execute a single physics step (internal method).

        Used by _run_simulation_rollout() and simulate() for granular control.
        Not intended for direct use by RL agents.
        """
        # Box2D Step signature: Step(timeStep, velocityIterations, positionIterations, particleIterations=0)
        # Warm starting is controlled by b2World.warmStarting property (set on world, not per-step)
        self.engine.world.Step(
            self.config.time_step,
            self.config.velocity_iters,
            self.config.position_iters,
        )
        self.engine.time_update(self.config.time_step)
        self.step_count += 1

    def _run_simulation_rollout(self):
        """
        Run physics simulation to completion.

        This is the core simulation loop that runs until success, failure, or timeout.
        """
        interventions = []

        for step_idx in range(self.max_steps):

            # Check for scheduled interventions (if enabled)
            if self.engine._intervention_scheduler is not None:
                self.engine._intervention_scheduler.check_triggers(step_idx, self.engine)

            # Physics step
            self._step_physics()

            # Render if renderer available
            self.render()

            # Check termination conditions
            success = self.level.success_condition(self.engine)
            terminated = success
            truncated = step_idx >= self.max_steps - 1

            # Terminate on success or truncated (max steps).
            #
            # NOTE: We intentionally do NOT terminate early when the world becomes
            # stationary. In earlier versions, rollouts could end as soon as the
            # simulation settled, which made episode lengths depend on low-level
            # dynamics and small engine changes. That variability broke "consistent
            # rollout semantics" for downstream consumers (e.g., training loops or
            # evaluation code that assume a fixed maximum horizon, align rollouts
            # by time step, or log per-step statistics across tasks).
            #
            # Keeping the loop running until success or max_steps ensures that:
            #   * rollouts for a given level always have the same maximum length,
            #   * time indices are comparable across runs and configurations, and
            #   * minor physics differences do not change control flow structure.
            # This trades some extra computation in stationary regimes for simpler,
            # more predictable rollout semantics.
            if success or truncated:
                break

        # Build final observation and info
        obs = self._get_observation()
        reward = self._calculate_reward(success, truncated)
        info = self._get_info_dict(success, terminated, truncated)
        info["interventions"] = interventions

        return obs, reward, terminated, truncated, info

    def _validate_action(
        self, action: Union[List[Tuple[float, float, float]], np.ndarray]
    ) -> List[Tuple[float, float, float]]:
        """Validate action format and convert to standard format."""
        if len(self.level.action_objects) == 0:
            if action != [] and not (
                isinstance(action, np.ndarray) and action.size == 0
            ):
                raise ValueError(
                    f"No action objects in level, but received action: {action}"
                )
            return []

        expected_dim = len(self.level.action_objects) * 3

        # Discrete action handling: indices mapped to the same bounds on a 0.1 grid
        if self.action_type == "discrete":
            # Ensure necessary discrete config exists
            x_bins, y_bins, s_bins = getattr(self, "_discrete_bins", (101, 101, 15))
            x_low, y_low, s_low = getattr(self, "_discrete_lows", (-5.0, -5.0, 0.1))
            step = getattr(self, "_discrete_step", 0.1)

            if isinstance(action, np.ndarray):
                if action.shape != (expected_dim,):
                    raise ValueError(
                        f"Expected action shape ({expected_dim},), got {action.shape}"
                    )
                indices = action.astype(np.int64).tolist()
            elif isinstance(action, list):
                if len(action) != len(self.level.action_objects):
                    raise ValueError(
                        f"Expected {len(self.level.action_objects)} action tuples, got {len(action)}"
                    )
                # Flatten list of 3-tuples
                indices = []
                for i, pos in enumerate(action):
                    if not isinstance(pos, (tuple, list)) or len(pos) != 3:
                        raise ValueError(
                            f"Action {i} must be a tuple/list of length 3 (x, y, size), got {pos}"
                        )
                    if not all(isinstance(v, (int, np.integer)) for v in pos):
                        raise ValueError(
                            f"Action {i} must contain integer indices for discrete mode, got {pos}"
                        )
                    indices.extend([int(pos[0]), int(pos[1]), int(pos[2])])
            else:
                raise ValueError(
                    f"Action must be list of tuples or numpy array, got {type(action)}"
                )

            # Bounds check and map indices to continuous values
            converted_action: List[Tuple[float, float, float]] = []
            for i in range(0, expected_dim, 3):
                xi, yi, si = int(indices[i]), int(indices[i + 1]), int(indices[i + 2])
                if not (0 <= xi < x_bins and 0 <= yi < y_bins and 0 <= si < s_bins):
                    raise ValueError(
                        f"Discrete indices out of bounds at object {i // 3}: {(xi, yi, si)}"
                    )
                # Round to PRECISION to avoid floating-point accumulation errors
                x = round(x_low + step * xi, PRECISION)
                y = round(y_low + step * yi, PRECISION)
                s = round(s_low + step * si, PRECISION)
                converted_action.append((float(x), float(y), float(s)))
        else:
            # Continuous action handling (existing behavior)
            if isinstance(action, np.ndarray):
                if action.shape != (expected_dim,):
                    raise ValueError(
                        f"Expected action shape ({expected_dim},), got {action.shape}"
                    )
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
                converted_action = [
                    (x, y, np.clip(s, 0.1, 1.5)) for (x, y, s) in action
                ]
            else:
                raise ValueError(
                    f"Action must be list of tuples or numpy array, got {type(action)}"
                )

        return converted_action

    def _validate_action_with_failure(
        self, action: Union[List[Tuple[float, float, float]], np.ndarray]
    ) -> Dict[str, Any]:
        """Validate action and return failure information instead of raising exceptions."""
        try:
            converted_action = self._validate_action(action)

            # Check placement validity for each action object
            for i, (x, y, radius) in enumerate(converted_action):
                if not self._is_valid_placement(x, y, radius):
                    return {
                        "invalid": True,
                        "action": None,
                        "error": f"Action object {i} at ({x:.2f}, {y:.2f}) with radius {radius:.2f} is invalid",
                    }

            return {"invalid": False, "action": converted_action, "error": None}
        except ValueError as e:
            return {"invalid": True, "action": None, "error": str(e)}

    def _is_valid_placement(self, x: float, y: float, radius: float) -> bool:
        """Check if placing an object at (x, y) with given radius is valid."""
        if not self._is_within_bounds(x, y, radius):
            return False
        if self._would_collide_with_objects(x, y, radius):
            return False
        return True

    def _is_within_bounds(self, x: float, y: float, radius: float) -> bool:
        """Check if object placement is within world boundaries."""
        min_x = -5.0 + radius
        max_x = 5.0 - radius
        min_y = -5.0 + radius
        max_y = 5.0 - radius
        return min_x <= x <= max_x and min_y <= y <= max_y

    def _would_collide_with_objects(self, x: float, y: float, radius: float) -> bool:
        """Check if object placement would collide with existing objects."""
        for name, obj in self.level.objects.items():
            if name in self.level.action_objects:
                continue

            if hasattr(obj, "radius"):
                distance = np.sqrt((x - obj.x) ** 2 + (y - obj.y) ** 2)
                if distance < (radius + obj.radius):  # type: ignore
                    return True
            elif hasattr(obj, "length"):
                if self._circle_intersects_bar(x, y, radius, obj):
                    return True
            elif hasattr(obj, "total_width"):
                if self._circle_intersects_basket(x, y, radius, obj):
                    return True

        return False

    def _circle_intersects_bar(self, cx: float, cy: float, radius: float, bar) -> bool:
        """Check if circle intersects with rotated bar using precise geometry."""
        # Transform circle center into bar's local coordinates
        angle_rad = np.radians(-bar.angle)  # negative for inverse rotation
        dx = cx - bar.x
        dy = cy - bar.y
        local_x = dx * np.cos(angle_rad) - dy * np.sin(angle_rad)
        local_y = dx * np.sin(angle_rad) + dy * np.cos(angle_rad)

        half_length = bar.length / 2
        half_thickness = bar.thickness / 2

        # Clamp local_x and local_y to the rectangle bounds
        closest_x = np.clip(local_x, -half_length, half_length)
        closest_y = np.clip(local_y, -half_thickness, half_thickness)

        # Compute distance from circle center to closest point on rectangle
        dist_sq = (local_x - closest_x) ** 2 + (local_y - closest_y) ** 2
        return dist_sq <= radius**2

    def _circle_intersects_basket(
        self, cx: float, cy: float, radius: float, basket
    ) -> bool:
        """Check if circle intersects with any basket wall (not the interior)."""
        half_width = basket.total_width / 2
        half_height = basket.total_height / 2
        # Use basket.wall_thickness if available, else default to 10% of min dimension
        wall_thickness = getattr(
            basket, "wall_thickness", 0.1 * min(basket.total_width, basket.total_height)
        )

        basket_left = basket.x - half_width
        basket_right = basket.x + half_width
        basket_bottom = basket.y - half_height
        basket_top = basket.y + half_height

        # Define rectangles for each wall: left, right, bottom, top
        walls = [
            # Left wall
            (basket_left, basket_bottom, basket_left + wall_thickness, basket_top),
            # Right wall
            (basket_right - wall_thickness, basket_bottom, basket_right, basket_top),
            # Bottom wall
            (basket_left, basket_bottom, basket_right, basket_bottom + wall_thickness),
            # Top wall
            (basket_left, basket_top - wall_thickness, basket_right, basket_top),
        ]

        for wall in walls:
            if self._circle_intersects_rect(cx, cy, radius, *wall):
                return True
        return False

    def _circle_intersects_rect(
        self,
        cx: float,
        cy: float,
        radius: float,
        left: float,
        bottom: float,
        right: float,
        top: float,
    ) -> bool:
        """Check if circle intersects with axis-aligned rectangle."""
        # Find the closest point to the circle within the rectangle
        closest_x = np.clip(cx, left, right)
        closest_y = np.clip(cy, bottom, top)
        # Calculate the distance between the circle's center and this closest point
        distance = np.sqrt((cx - closest_x) ** 2 + (cy - closest_y) ** 2)
        return distance < radius

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
        """Get image observation by rendering current simulation state."""
        from interphyre.render import OpenCVRenderer

        width, height = self.image_size

        world_size = 10.0
        target_ppm = min(width, height) / world_size
        ppm = min(target_ppm, self.image_ppm)

        renderer = OpenCVRenderer(width=width, height=height, ppm=ppm)

        if self.discrete_colors:
            image = renderer.render_discrete(self.engine)
        else:
            image = renderer.render(self.engine)

        renderer.close()
        return image

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
        # Ensure terminated and truncated are mutually exclusive (gym standard)
        if terminated and truncated:
            truncated = False  # Success takes precedence over timeout

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
        steps: Optional[int] = None,
        return_trace: bool = False,
        verbose: bool = False,
    ) -> Optional[List[Tuple[Any, float, bool, bool, Dict[str, Any]]]]:
        """
        Public method for debugging/profiling: run simulation with custom parameters.

        Unlike step(), this can be called multiple times and doesn't affect episode state.
        Useful for performance profiling, visualization, and debugging.

        Note: This method does NOT apply interventions - use step() for that.

        Args:
            steps: Maximum number of steps to simulate (default: config.max_steps)
            return_trace: Whether to return the full trace of (obs, reward, terminated, truncated, info)
            verbose: Whether to print progress information

        Returns:
            List of (observation, reward, terminated, truncated, info) tuples if return_trace=True,
            otherwise None

        """
        if steps is None:
            steps = self.config.max_steps

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
            # Use the new _step_physics() method for consistency
            self._step_physics()

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
