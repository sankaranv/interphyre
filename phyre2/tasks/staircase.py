from phyre2.level_builder import PHYRETemplate
from phyre2.objects import Ball, Basket, Platform
import numpy as np


class Staircase(PHYRETemplate):
    def __init__(self):
        super().__init__()

    def build_task(self):
        self.name = "staircase"
        self.description = (
            "Make sure the green ball goes through the funnel and hits the purple pad"
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
            "stair_1_platform": Platform(-4.5, 3, 0.7, -5, "black", False),
            "stair_2_platform": Platform(-2.5, 2.1, 0.7, -5, "black", False),
            "stair_3_platform": Platform(-0.5, 1.2, 0.7, -5, "black", False),
            "stair_4_platform": Platform(1.5, 0.3, 0.7, -5, "black", False),
            "stair_5_platform": Platform(3.5, -0.6, 0.7, -5, "black", False),
            "left_barrier_platform": Platform(0, -4.5, 1, 90, "black", False),
            "right_barrier_platform": Platform(0, -4.5, 1, 90, "black", False),
            "basket": Basket(0, 0, 2, 0, "purple", True),
        }

        # Randomly set basket attributes
        self.objects["basket"].scale = np.random.uniform(1, 2.5)
        # self.objects["basket"].x = np.random.uniform(-2.5, 2.5)
        self.objects["basket"].y = -5 + self.objects["basket"].scale * 0.083

        # Randomly set barrier attributes
        self.objects["left_barrier_platform"].length = (
            self.objects["basket"].scale * 1.5
        )
        self.objects["right_barrier_platform"].length = (
            self.objects["basket"].scale * 1.5
        )
        self.objects["left_barrier_platform"].x = (
            self.objects["basket"].x - self.objects["basket"].scale * 0.83
        )
        self.objects["right_barrier_platform"].x = (
            self.objects["basket"].x + self.objects["basket"].scale * 0.83
        )

        # Randomly set green ball starting position
        self.objects["green_ball"].x = np.random.uniform(-4, 4)
        self.objects["green_ball"].radius = np.random.uniform(0.25, 0.4)

        # Randomly set red ball starting position
        # This only matters for passive mode
        self.objects["red_ball"].x = np.random.uniform(-2.5, 4.5)
        self.objects["red_ball"].y = np.random.uniform(-2, 4)
