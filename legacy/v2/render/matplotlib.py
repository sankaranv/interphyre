import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
from phyre2.core.level import Level
from phyre2.render.base import Renderer
from typing import Any


system_colors = {
    "green": "#20C9A2",
    "red": "#EB5234",
    "blue": "#205DD6",
    "black": "#000000",
    "gray": "#C8C8C8",
    "purple": "#513896",
    "yellow": "#FFD343",
    "white": "#FFFFFF",
}


class MatplotlibRenderer(Renderer):
    def __init__(self, screen_size: int = 600, ppm: int = 60):
        self.screen_size = screen_size
        self.ppm = ppm
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.ax.set_xlim(0, screen_size)
        self.ax.set_ylim(0, screen_size)
        self.ax.set_aspect("equal")
        self.ax.axis("off")

    def render(self, level: Level, state: Any):
        self.ax.clear()
        self.ax.set_xlim(0, self.screen_size)
        self.ax.set_ylim(0, self.screen_size)
        self.ax.set_aspect("equal")
        self.ax.axis("off")

        for name, obj in level.objects.items():
            if name not in state:
                continue

            x, y = state[name]
            x_px = x * self.ppm
            y_px = self.screen_size - y * self.ppm
            color = system_colors.get((obj.color or "gray").lower(), "#C8C8C8")

            if obj.type == "ball":
                radius = obj.size if isinstance(obj.size, float) else obj.size[0]
                circle = patches.Circle((x_px, y_px), radius * self.ppm, color=color)
                self.ax.add_patch(circle)

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
                    [
                        x_px + px * math.cos(angle_rad) - py * math.sin(angle_rad),
                        y_px + px * math.sin(angle_rad) + py * math.cos(angle_rad),
                    ]
                    for px, py in corners
                ]

                polygon = patches.Polygon(rotated, closed=True, color=color)
                self.ax.add_patch(polygon)

        plt.pause(0.001)
        plt.draw()

    def close(self):
        plt.close(self.fig)
