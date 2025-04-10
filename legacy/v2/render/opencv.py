import numpy as np
import cv2
import math
from phyre2.core.level import Level
from phyre2.render.base import Renderer
from typing import Any


system_colors = {
    "green": (32, 201, 162),
    "red": (235, 82, 52),
    "blue": (32, 93, 214),
    "black": (0, 0, 0),
    "gray": (200, 200, 200),
    "purple": (81, 56, 150),
    "yellow": (255, 211, 67),
    "white": (255, 255, 255),
}


class OpenCVRenderer(Renderer):
    def __init__(self, screen_size: int = 600, ppm: int = 60):
        self.screen_size = screen_size
        self.ppm = ppm
        self.background_color = (255, 255, 255)
        self.image = np.ones((screen_size, screen_size, 3), dtype=np.uint8) * 255

    def render(self, level: Level, state: Any):
        self.image[:] = self.background_color

        for name, obj in level.objects.items():
            if name not in state:
                continue

            x, y = state[name]
            x_px = int(x * self.ppm)
            y_px = int(self.screen_size - y * self.ppm)
            color = system_colors.get((obj.color or "gray").lower(), (200, 200, 200))

            if obj.type == "ball":
                radius = (
                    int(obj.size * self.ppm)
                    if isinstance(obj.size, float)
                    else int(obj.size[0] * self.ppm)
                )
                cv2.circle(self.image, (x_px, y_px), radius, color, -1)

            elif obj.type in ["platform", "basket"]:
                width, height = (
                    obj.size if isinstance(obj.size, list) else (obj.size, obj.size)
                )
                w_px = width * self.ppm
                h_px = height * self.ppm
                angle_rad = -math.radians(obj.angle)

                # Define corners centered at (0, 0)
                dx, dy = w_px / 2, h_px / 2
                corners = [[-dx, -dy], [dx, -dy], [dx, dy], [-dx, dy]]

                # Rotate and translate corners
                rotated = [
                    [
                        int(x_px + px * math.cos(angle_rad) - py * math.sin(angle_rad)),
                        int(y_px + px * math.sin(angle_rad) + py * math.cos(angle_rad)),
                    ]
                    for px, py in corners
                ]

                pts = np.array(rotated, np.int32).reshape((-1, 1, 2))
                cv2.fillPoly(self.image, [pts], color)

        cv2.imshow("PHYRE OpenCV Renderer", self.image)
        cv2.waitKey(1)

    def close(self):
        cv2.destroyAllWindows()
