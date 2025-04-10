from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from phyre2.core.level import Level


class PhysicsEngine(ABC):
    @abstractmethod
    def load_level(self, level: Level):
        pass

    @abstractmethod
    def step(self, action: Optional[Dict[str, Any]] = None):
        pass

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def get_state(self) -> Any:
        pass

    @abstractmethod
    def is_goal_achieved(self) -> bool:
        pass

    @abstractmethod
    def objects(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def is_stationary_world(self) -> bool:
        pass

    @abstractmethod
    def close(self):
        pass


def select_engine(name: str, ppm: int = 60, fps: int = 60) -> PhysicsEngine:
    name = name.lower()
    if name == "box2d":
        from phyre2.physics.box2d import Box2DEngine

        return Box2DEngine(ppm=ppm, fps=fps)
    else:
        raise ValueError(f"Unknown physics engine: {name}")
