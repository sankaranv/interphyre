import cv2
import numpy as np
from typing import Tuple, Optional
from interphyre.render.base import Renderer, COLORS
from Box2D import b2PolygonShape, b2CircleShape


class OpenCVRenderer(Renderer):
    """OpenCV-based renderer for generating images of physics simulations.

    This renderer uses OpenCV to create images of the physics simulation
    without requiring a display window. It's optimized for generating
    images for machine learning agents and can run on headless servers.

    Attributes:
        width (int): Width of the rendered image in pixels
        height (int): Height of the rendered image in pixels
        ppm (float): Pixels per Box2D unit (scaling factor)
        image (np.ndarray): Current rendered image buffer
    """

    def __init__(self, width: int = 600, height: int = 600, ppm: float = 60):
        """Initialize the OpenCV renderer.

        Args:
            width: Width of the image in pixels (default: 600)
            height: Height of the image in pixels (default: 600)
            ppm: Pixels per Box2D unit (scaling factor) (default: 60)
        """
        self.width = width
        self.height = height
        self.ppm = ppm
        self.image = np.zeros((height, width, 3), dtype=np.uint8)

    def world_to_screen(self, position: Tuple[float, float]) -> Tuple[int, int]:
        """
        Convert a point from Box2D world coordinates to image coordinates.

        This version places the origin in the center of the image:
            screen_x = int(x * ppm + width/2)
            screen_y = int(-y * ppm + height/2)

        Parameters:
            position (Tuple[float, float]): (x, y) in world coordinates.

        Returns:
            Tuple[int, int]: The corresponding image (x, y) position.
        """
        x, y = position
        screen_x = int(x * self.ppm + self.width / 2)
        screen_y = int(-y * self.ppm + self.height / 2)
        return screen_x, screen_y

    def _get_object_color(self, body, engine) -> Tuple[int, int, int]:
        """
        Retrieve the drawing color for a given body from the level file.

        Assumes:
          - body.userData stores the object's name.
          - engine.level.objects maps names to level objects with a 'color' attribute.
        If the name is not found (e.g. walls), a default color is returned.
        """
        if engine.level is None:
            return COLORS["black"]
        name = body.userData
        if name not in engine.level.objects:
            if "wall" in str(name).lower():
                return (255, 0, 0)  # render walls in red
            return COLORS["black"]
        obj = engine.level.objects.get(name)
        if obj is None or not hasattr(obj, "color"):
            return COLORS["black"]
        return COLORS.get(obj.color.lower(), COLORS["black"])

    def render(self, engine) -> np.ndarray:
        """
        Render the current state of the simulation to an image.

        Each fixture is rendered after applying the body transform to its local coordinates.

        Args:
            engine: The Box2DEngine containing the physics world to render

        Returns:
            np.ndarray: RGB image as numpy array (height, width, 3)
        """
        # Clear image using white background
        self.image.fill(255)

        # Iterate over bodies
        for name, body in engine.bodies.items():
            color = self._get_object_color(body, engine)
            for fixture in body.fixtures:

                # Do not render sensor fixtures
                if fixture.sensor:
                    continue

                shape = fixture.shape
                if isinstance(shape, b2CircleShape):
                    # For circle shapes: transform the center and draw
                    position = body.transform * shape.pos
                    radius = int(shape.radius * self.ppm)
                    screen_pos = self.world_to_screen((position[0], position[1]))

                    cv2.circle(self.image, screen_pos, radius, color, -1)

                elif isinstance(shape, b2PolygonShape):
                    # For polygon shapes: transform each vertex
                    vertices = [body.transform * v for v in shape.vertices]
                    pts = np.array(
                        [self.world_to_screen((v[0], v[1])) for v in vertices],
                        dtype=np.int32,
                    )

                    cv2.fillPoly(self.image, [pts], color)
                else:
                    raise ValueError(f"Unsupported shape type: {type(shape)}")

        return self.image.copy()

    def close(self) -> None:
        """Close and clean up any resources used by the renderer."""
        # OpenCV doesn't require explicit cleanup for basic operations
        pass

    def wait(self, duration: int) -> None:
        """Wait for specified duration (for compatibility with PygameRenderer)."""
        import time
        time.sleep(duration / 1000.0)  # Convert milliseconds to seconds