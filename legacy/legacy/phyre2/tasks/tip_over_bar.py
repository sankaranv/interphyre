from phyre2.level_builder import PHYRETemplate
from phyre2.objects import Ball, Basket, Platform
import numpy as np


class TipOverBar(PHYRETemplate):
    def __init__(self):
        super().__init__()

    def build_task(self):
        self.name = "tip_over_bar"
        self.description = "Tip the bar over so it hits the ground"

        # Set level properties
        self.target_object = "green_platform"
        self.goal_object = "purple_platform"
        self.action_objects = ["red_ball"]

        # Ball attributes are x, y, radius, color, dynamic
        # Platform attributes are x, y, length, angle, color, dynamic
        # Basket attributes are x, y, scale, color, dynamic
        # Set fixed attributes
        self.objects = {
            "green_platform": Platform(0, -4.8, 1, 90, "green", True),
            "red_ball": Ball(0, 0, 0.4, "red", True),
            "black_platform": Platform(0, -4.8, 1, 0, "black", False),
            "purple_platform": Platform(0, -4.95, 5, 0, "purple", False),
            "ceiling_platform": Platform(0, 0, 5, 0, "black", False),
        }

        # Randomly set black platform attributes
        self.objects["black_platform"].length = np.random.uniform(2, 4)
        self.objects["black_platform"].x = np.random.uniform(-1.5, 1.5)
        self.objects["black_platform"].y = np.random.uniform(-3, 3)

        # Randomly set green bar attributes
        self.objects["green_platform"].length = np.random.uniform(1, 1.5)
        self.objects["green_platform"].x = self.objects[
            "black_platform"
        ].x + np.random.choice([-1, 1]) * (self.objects["black_platform"].length - 0.1)
        self.objects["green_platform"].y = (
            self.objects["black_platform"].y
            + self.objects["green_platform"].length
            + 0.1
        )

        # Randomly set ceiling height
        self.objects["ceiling_platform"].y = self.objects[
            "black_platform"
        ].y + np.random.uniform(
            self.objects["green_platform"].length + 1.5,
            self.objects["green_platform"].length + 3,
        )
        self.objects["ceiling_platform"].y = np.clip(
            self.objects["ceiling_platform"].y, -4.99, 4.99
        )

        # Randomly set red ball starting position
        # This only matters for passive mode
        self.objects["red_ball"].x = np.random.uniform(-4.5, 4.5)
        self.objects["red_ball"].y = np.random.uniform(-2, 4)
