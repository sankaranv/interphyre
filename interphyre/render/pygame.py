import pygame
from typing import Tuple
from interphyre.render.base import Renderer, COLORS
from Box2D import b2PolygonShape, b2CircleShape


class PygameRenderer(Renderer):
    def __init__(self, width: int = 600, height: int = 600, ppm: float = 60):
        """
        Initialize the Pygame renderer.

        Parameters:
            width (int): Width of the window in pixels.
            height (int): Height of the window in pixels.
            ppm (float): Pixels per Box2D unit (scaling factor).
        """
        pygame.init()
        self.width = width
        self.height = height
        self.ppm = ppm  # pixels per unit
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Interphyre Simulation")
        self.clock = pygame.time.Clock()
        self.fps = 60  # Frames per second for rendering

        # TODO - support different sizes using the screen_size / self.ppm * 0.5 conversion

    def world_to_screen(self, position: Tuple[float, float]) -> Tuple[int, int]:
        """
        Convert a point from Box2D world coordinates to Pygame screen coordinates.

        This version places the origin in the center of the window:
            screen_x = int(x * ppm + width/2)
            screen_y = int(-y * ppm + height/2)

        Parameters:
            position (Tuple[float, float]): (x, y) in world coordinates.

        Returns:
            Tuple[int, int]: The corresponding screen (x, y) position.
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

    def render(self, engine) -> None:
        """
        Render the current state of the simulation.

        Each fixture is rendered after applying the body transform to its local coordinates.
        """
        # Clear screen using white
        self.screen.fill(COLORS["white"])

        # Iterate over bodies
        for name, body in engine.bodies.items():
            color = self._get_object_color(body, engine)
            for fixture in body.fixtures:

                # Do not render sensor fixtures, they are only used for detection and measurement purposes
                if fixture.sensor:
                    color = (255, 0, 0)

                shape = fixture.shape
                if isinstance(shape, b2CircleShape):
                    # For circle shapes: transform the center and draw
                    position = body.transform * shape.pos
                    radius = shape.radius * self.ppm
                    screen_pos = self.world_to_screen((position[0], position[1]))
                    pygame.draw.circle(
                        self.screen,
                        color,
                        screen_pos,
                        radius,
                    )
                elif isinstance(shape, b2PolygonShape):
                    # For polygon shapes: transform each vertex
                    vertices = [body.transform * v for v in shape.vertices]
                    pts = [self.world_to_screen((v[0], v[1])) for v in vertices]
                    pygame.draw.polygon(self.screen, color, pts)
                else:
                    raise ValueError(f"Unsupported shape type: {type(shape)}")

        pygame.display.flip()
        pygame.event.pump()
        self.clock.tick(self.fps)

        # Exit if the window is closed
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                exit()

    def close(self) -> None:
        pygame.quit()

    def wait(self, duration: int) -> None:
        pygame.time.wait(duration)
