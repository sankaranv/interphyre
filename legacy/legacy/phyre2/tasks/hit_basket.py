from phyre2.level_builder import PHYRETemplate
from phyre2.objects import Ball, Basket, Platform
import numpy as np


class HitBasket(PHYRETemplate):
    def __init__(self):
        super().__init__()

    def build_task(self):
        self.name = "hit_basket"
        self.description = (
            "Make sure the green ball hits the ground and stays out of the basket"
        )

        # Set level properties
        self.target_object = "green_ball"
        self.goal_object = "basket"
        self.action_objects = ["red_ball"]

        # Ball attributes are x, y, radius, color, dynamic
        # Platform attributes are x, y, length, angle, color, dynamic
        # Basket attributes are x, y, scale, color, dynamic
        # Set fixed attributes
        self.objects = {
            "green_ball": Ball(0, 4.9, 1, "green", True),
            "red_ball": Ball(0, 0, 0.4, "red", True),
            "left_platform": Platform(-3, 0, 2, 0, "black", False),
            "right_platform": Platform(3, 0, 2, 0, "black", False),
            "angled_platform": Platform(0, -3.9, 5.5, 10, "black", False),
            "basket": Basket(0, -4.9, 0.7, 180, "blue", True),
        }

        # Randomly set beam height
        self.objects["left_platform"].y = np.random.uniform(-0.5, 1)
        self.objects["right_platform"].y = self.objects["left_platform"].y

        # Set basket starting position
        self.objects["basket"].x = np.random.uniform(-0.5, 0.5)
        self.objects["basket"].y = self.objects["left_platform"].y + np.random.uniform(
            1, 2
        )

        # Randomly set green ball attributes
        self.objects["green_ball"].radius = np.random.uniform(0.2, 0.5)
        self.objects["green_ball"].x = np.random.choice(
            [np.random.uniform(-4.5, -1.5), np.random.uniform(1.5, 4.5)]
        )
        self.objects["green_ball"].y = (
            self.objects["left_platform"].y + self.objects["green_ball"].radius
        )

        # Randomly set red ball starting position
        # This only matters for passive mode
        self.objects["red_ball"].x = np.random.uniform(-4.5, 4.5)
        self.objects["red_ball"].y = np.random.uniform(-2, 4)
