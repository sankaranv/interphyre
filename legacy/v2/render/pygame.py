import pygame
import math
from typing import Any
from phyre2.core.level import Level
from phyre2.render.base import Renderer
from phyre2.physics.box2d import Box2DEngine

COLOR_MAP = {
    "green": (32, 201, 162),
    "red": (235, 82, 52),
    "blue": (32, 93, 214),
    "black": (0, 0, 0),
    "gray": (200, 200, 200),
    "purple": (81, 56, 150),
    "yellow": (255, 211, 67),
    "white": (255, 255, 255),
}


class PygameRenderer(Renderer):
    def __init__(
        self,
        screen_width: int = 600,
        screen_height: int = 600,
        ppm: int = 60,
    ):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.ppm = ppm
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("PHYRE Renderer")
        self.clock = pygame.time.Clock()

    def process_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True

    def _to_screen_coords(self, pos):
        x, y = pos
        x_px = int(x * self.ppm + self.screen_width / 2)
        y_px = int(self.screen_height - (y * self.ppm))
        return x_px, y_px

    def render(self, level: Level, state: Any, engine: Box2DEngine = None):
        self.screen.fill(system_colors["white"])

        for name, obj in level.objects.items():
            color = system_colors.get(
                (obj.color or "gray").lower(), system_colors["gray"]
            )

            if engine is not None and name in engine.objects():
                body = engine.objects()[name]
                if obj.type == "ball":
                    for fixture in body.fixtures:
                        shape = fixture.shape
                        pos = body.transform * shape.pos
                        x_px, y_px = self._to_screen_coords((pos.x, pos.y))
                        pygame.draw.circle(
                            self.screen,
                            color,
                            (x_px, y_px),
                            int(shape.radius * self.ppm),
                        )
                elif obj.type in ["platform", "basket"]:
                    for fixture in body.fixtures:
                        shape = fixture.shape
                        vertices = [(body.transform * v) for v in shape.vertices]
                        pixel_verts = [
                            self._to_screen_coords((v.x, v.y)) for v in vertices
                        ]
                        pygame.draw.polygon(self.screen, color, pixel_verts)
            elif name in state:
                x, y = state[name]
                x_px, y_px = self._to_screen_coords((x, y))
                if obj.type == "ball":
                    radius = int(
                        (obj.size if isinstance(obj.size, float) else obj.size[0])
                        * self.ppm
                    )
                    pygame.draw.circle(self.screen, color, (x_px, y_px), radius)
                elif obj.type in ["platform", "basket"]:
                    width, height = (
                        obj.size if isinstance(obj.size, list) else (obj.size, obj.size)
                    )
                    w_px = width * self.ppm
                    h_px = height * self.ppm
                    angle_rad = -math.radians(obj.angle)
                    dx, dy = w_px / 2, h_px / 2
                    corners = [[-dx, -dy], [dx, -dy], [dx, dy], [-dx, dy]]
                    rotated = [
                        (
                            int(
                                x_px
                                + px * math.cos(angle_rad)
                                - py * math.sin(angle_rad)
                            ),
                            int(
                                y_px
                                + px * math.sin(angle_rad)
                                + py * math.cos(angle_rad)
                            ),
                        )
                        for px, py in corners
                    ]
                    pygame.draw.polygon(self.screen, color, rotated)

        pygame.display.flip()
        pygame.event.pump()
        self.clock.tick(60)
        # Check for quit event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True

    def close(self):
        pygame.quit()
