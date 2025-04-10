from abc import ABC, abstractmethod

COLORS = {
    "green": (32, 201, 162),
    "red": (235, 82, 52),
    "blue": (32, 93, 214),
    "black": (0, 0, 0),
    "gray": (200, 200, 200),
    "purple": (81, 56, 150),
    "yellow": (255, 211, 67),
    "white": (255, 255, 255),
}


class Renderer(ABC):
    @abstractmethod
    def render(self, engine) -> None:
        """
        Render the current state of the engine (simulation world).
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close and clean up any resources used by the renderer.
        """
        pass
