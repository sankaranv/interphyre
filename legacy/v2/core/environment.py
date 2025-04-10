import gymnasium as gym
import numpy as np
from typing import Dict, Any, Optional
from phyre2.core.level import Level
from phyre2.physics.engine import select_engine, PhysicsEngine
from phyre2.render.base import Renderer


class PhyreEnv(gym.Env):
    def __init__(
        self,
        level: Level,
        engine_name: str = "box2d",
        renderer: Optional[Renderer] = None,
        screen_size: int = 600,
        ppm: int = 60,
        max_steps: int = 500,
        fps: int = 60,
    ):
        super().__init__()
        self.level = level
        self.renderer = renderer
        self.engine: PhysicsEngine = select_engine(engine_name, ppm=ppm, fps=fps)
        self.engine.load_level(level)

        self.screen_size = screen_size
        self.ppm = ppm
        self.max_steps = max_steps
        self.fps = fps
        self.step_count = 0

        # Action space: placement positions for action_objects
        num_action_objects = len(level.action_objects)
        low = np.array(
            [-screen_size / ppm / 2, -screen_size / ppm / 2] * num_action_objects
        )
        high = np.array(
            [screen_size / ppm / 2, screen_size / ppm / 2] * num_action_objects
        )
        self.action_space = gym.spaces.Box(low=low, high=high, dtype=np.float32)

        # Observation: object positions (x, y)
        self.observation_space = gym.spaces.Box(
            low=-np.inf, high=np.inf, shape=(len(level.objects), 2), dtype=np.float32
        )

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.engine.reset()
        self.step_count = 0
        return self._get_observation(), {}

    def get_reward(self):
        return 1.0 if self.engine.is_goal_achieved() else 0.0

    def step(self, action=None):
        self.engine.step(action)
        self.step_count += 1
        obs = self._get_observation()
        reward = self.get_reward()
        truncated = False
        done = (
            self.engine.is_goal_achieved()
            or self.step_count >= self.max_steps
            or self.engine.is_stationary_world()
        )
        info = {}
        if self.renderer:
            state = self.engine.get_state()
            self.renderer.render(self.level, state, self.engine)

        if done:
            if self.engine.is_goal_achieved():
                info["termination"] = "goal"
            elif self.engine.is_stationary_world():
                info["termination"] = "stationary_world"
                truncated = True
            elif self.step_count >= self.max_steps:
                info["termination"] = "max_steps"
                truncated = True
            else:
                info["termination"] = "unknown"
        else:
            info["termination"] = "not_done"
        return obs, reward, done, truncated, info

    def _get_observation(self):
        return np.array(list(self.engine.get_state().values()), dtype=np.float32)

    def simulate(self):
        clock = self.renderer.clock
        trace = []
        for _ in range(self.max_steps):
            render_status = self.render()
            if not render_status:
                break
            obs, reward, done, truncated, info = self.step()
            trace.append((obs, reward, done, truncated, info))
            clock.tick(self.fps)
            if done:
                break
        return trace

    def render(self):
        if self.renderer:
            state = self.engine.get_state()
            done = self.renderer.render(self.level, state, self.engine)
        return done

    def close(self):
        self.engine.close()
        if self.renderer:
            self.renderer.close()
