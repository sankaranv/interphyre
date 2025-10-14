from abc import ABC, abstractmethod

# Color palette for rendering objects
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
    """Abstract base class for rendering physics simulations.

    This class defines the interface that all renderers must implement
    to visualize the physics simulation. Renderers handle the conversion
    from physics world coordinates to screen coordinates and drawing
    of all objects in the simulation.
    """

    @abstractmethod
    def render(self, engine) -> None:
        """Render the current state of the physics simulation.

        Args:
            engine: The Box2DEngine containing the physics world to render
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close and clean up any resources used by the renderer.

        This method should be called when the renderer is no longer needed
        to properly clean up resources like windows, contexts, etc.
        """
        pass
