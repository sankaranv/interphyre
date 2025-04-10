from phyre2.level_builder import PHYRETemplate
from phyre2.objects import Ball, Basket, Platform
import numpy as np


class AvoidBasket(PHYRETemplate):
    def __init__(self):
        super().__init__()

    def build_task(self):
        self.name = "avoid_basket"
        self.description = (
            "Make sure the green ball hits the ground and stays out of the basket"
        )

        # Set level properties
        self.target_object = "green_ball"
        self.goal_object = "purple_platform"
        self.action_objects = ["red_ball"]

        # Ball attributes are x, y, radius, color, dynamic
        # Platform attributes are x, y, length, angle, color, dynamic
        # Basket attributes are x, y, scale, color, dynamic
        # Set fixed attributes
        self.objects = {
            "green_ball": Ball(0, 4.9, 1, "green", True),
            "red_ball": Ball(0, 0, 0.4, "red", True),
            "purple_platform": Platform(0, -4.9, 5, 0, "purple", False),
            "basket": Basket(0, -4.9, 1, "gray", True),
        }

        # Randomly set green ball attributes
        self.objects["green_ball"].x = np.random.uniform(-4.5, 4.5)
        self.objects["green_ball"].y = np.random.uniform(0.5, 4.5)
        self.objects["green_ball"].radius = np.random.uniform(0.2, 0.5)

        # Set basket starting position
        self.objects["basket"].x = self.objects["green_ball"].x
        self.objects["basket"].y = (
            -4.9 + self.objects["basket"].scale + np.random.uniform(0, 1)
        )
        self.objects["basket"].scale = np.random.uniform(0.5, 1.5)

        # Randomly set red ball starting position
        # This only matters for passive mode
        self.objects["red_ball"].x = np.random.uniform(-4.5, 4.5)
        self.objects["red_ball"].y = np.random.uniform(-2, 4)
