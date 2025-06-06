from typing import Optional, Tuple, List, Union
import gymnasium as gym
import numpy as np

from interphyre.engine import Box2DEngine
from interphyre.level import Level
from interphyre.render import Renderer


class PhyreEnv(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": 30}

    def __init__(self, level: Level, renderer: Optional[Renderer] = None):
        super().__init__()
        self.level = level
        self.renderer = renderer
        self.engine = Box2DEngine()
        self.action_placed = False
        self.current_obs = None
        self.current_state = None
        self.fps: int = 60
        self.time_step: float = 1 / self.fps
        self.velocity_iters: int = 6
        self.position_iters: int = 2
        self.obs_size: Tuple[int, int] = (600, 600)

        self.action_space = gym.spaces.Box(
            low=-5.0, high=5.0, shape=(len(level.action_objects), 2), dtype=np.float32
        )
        self.observation_space = gym.spaces.Box(
            low=0,
            high=255,
            shape=(self.obs_size[0], self.obs_size[1], 3),
            dtype=np.uint8,
        )

    def reset(self, seed: Optional[int] = None, options: Optional[dict] = None):
        super().reset(seed=seed)
        self.engine.reset(self.level)
        self.action_placed = False
        self.current_state = self.engine.get_state()
        return self.current_state, {}

    def step(self, action: List[Tuple[Union[int, float], Union[int, float]]]):
        if not self.action_placed:
            self.engine.place_action_objects(action)
            self.action_placed = True

        self.current_state = self.engine.get_state()

        done = self.level.success_condition(self.engine)
        reward = float(done)
        info = {"status": "running"}
        terminated = False
        return self.current_state, reward, done, terminated, info

    def simulate(
        self,
        steps: int = 1000,
        return_trace: bool = False,
        verbose: bool = False,
    ):
        if self.engine.world is None:
            raise ValueError(
                "World is not initialized. Call reset() before simulating."
            )
        trace = []
        status = "running"
        terminated = False
        for i in range(steps):
            self.engine.world.Step(
                self.time_step, self.velocity_iters, self.position_iters
            )
            self.engine.time_update(self.time_step)
            done = self.level.success_condition(self.engine)
            if done:
                status = "success"
            elif self.engine.world_is_stationary():
                status = "world_is_stationary"
                # terminated = True
            elif i == steps - 1:
                status = "timeout"
                terminated = True

            if return_trace:
                self.current_obs = self.engine.get_state()
                reward = float(done)
                info = {"status": status}
                trace.append((self.current_obs, reward, done, terminated, info))

            # Render the current state if a renderer is provided
            self.render()

            if verbose:
                print(f"Step {i+1}/{steps}, status: {status}")
            if done or terminated:
                break
        return trace

    def render(self):
        if self.renderer:
            self.renderer.render(self.engine)

    def close(self):
        if self.renderer:
            self.renderer.close()
