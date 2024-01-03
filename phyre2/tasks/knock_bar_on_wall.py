from phyre2.level_builder import PHYRETemplate
from phyre2.objects import Ball, Basket, Platform
import numpy as np


class KnockBarOnWall(PHYRETemplate):
    def __init__(self):
        super().__init__()

    def build_task(self):
        self.name = "ball_hit_wall"
        self.description = "Make the green ball hit the left or right wall"

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
            "purple_platform": Platform(0, 0, 5, 90, "purple", False),
            "basket": Basket(0, -4.9, 1, "gray", True),
        }

        # Randomly set purple platform to be the left or right wall
        self.objects["purple_platform"].x = np.random.choice([-4.9, 4.9])

        # Randomly set green bar starting position
        self.objects["green_platform"].x = np.random.uniform(-2, 2)
        self.objects["green_platform"].length = np.random.uniform(1, 4)
        self.objects["green_platform"].y = (
            -4.9 + self.objects["green_platform"].length / 2
        )

        # Set basket starting position
        self.objects["basket"].x = self.objects["green_platform"].x

        # Randomly set red ball starting position
        # This only matters for passive mode
        self.objects["red_ball"].x = np.random.uniform(-4.5, 4.5)
        self.objects["red_ball"].y = np.random.uniform(-2, 4)
