from abc import ABC, abstractmethod
from typing import Any
from phyre2.core.level import Level


class Renderer(ABC):
    @abstractmethod
    def render(self, level: Level, state: Any, engine: Any):
        pass

    @abstractmethod
    def close(self):
        pass
