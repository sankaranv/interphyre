from phyre2.level_builder import PHYRETemplate
from phyre2.objects import Ball, Basket, Platform
import numpy as np


class FunnelOntoPad(PHYRETemplate):
    def __init__(self):
        super().__init__()

    def build_task(self):
        self.name = "funnel_onto_pad"
        self.description = (
            "Make sure the green ball goes through the funnel and hits the purple pad"
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
            "left_funnel_platform": Platform(-3, 0, 2.65, -25, "black", False),
            "right_funnel_platform": Platform(3, 0, 2.65, 25, "black", False),
            "black_platform": Platform(0, -4.8, 1, 0, "black", False),
            "purple_platform": Platform(0, -4.95, 1, 0, "purple", False),
            "ground_platform": Platform(0, -4.95, 4, 0, "black", False),
        }

        # Randomly set beam height
        self.objects["left_funnel_platform"].y = np.random.uniform(1.5, 3)
        self.objects["right_funnel_platform"].y = self.objects["left_funnel_platform"].y

        # Randomly set ball attributes
        self.objects["green_ball"].radius = np.random.uniform(0.2, 0.3)
        self.objects["green_ball"].x = np.random.uniform(-0.5, 0.5)

        # Set purple platform starting position
        self.objects["purple_platform"].x = np.random.choice([-4.0, 4.0])
        self.objects["ground_platform"].x = -np.sign(self.objects["purple_platform"].x)
        self.objects["black_platform"].x = (
            np.sign(self.objects["purple_platform"].x) * 2.0
        )

        # Randomly set red ball starting position
        # This only matters for passive mode
        self.objects["red_ball"].x = np.random.uniform(-4.5, 4.5)
        self.objects["red_ball"].y = np.random.uniform(-2, 4)
