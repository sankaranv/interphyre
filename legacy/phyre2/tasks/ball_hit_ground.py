from phyre2.level_builder import PHYRETemplate
from phyre2.objects import Ball, Basket, Platform
import numpy as np


class BallHitGround(PHYRETemplate):
    def __init__(self):
        super().__init__()

    def build_task(self):
        self.name = "ball_hit_ground"
        self.description = "Make the green ball hit the ground"

        # Set level properties
        self.target_object = "green_ball"
        self.goal_object = "purple_platform"
        self.action_objects = ["red_ball"]

        # Ball attributes are x, y, radius, color, dynamic
        # Platform attributes are x, y, length, angle, color, dynamic
        # Set fixed attributes
        self.objects = {
            "green_ball": Ball(0, 4.9, 1, "green", True),
            "red_ball": Ball(0, 0, 0.5, "red", True),
            "purple_platform": Platform(0, -4.9, 10, 0, "purple", False),
            "high_platform": Platform(0, 0, 1, 0, "black", False),
        }

        # Randomly set high platform attributes
        self.objects["high_platform"].x = np.random.uniform(-2, 2)
        self.objects["high_platform"].y = np.random.uniform(-3, 3)
        self.objects["high_platform"].length = np.random.uniform(0.5, 2)

        # Randomly set green ball radius and place above the middle of the platform
        self.objects["green_ball"].x = self.objects["high_platform"].x / 2
        self.objects["green_ball"].radius = np.random.uniform(0.2, 0.45)

        # Randomly set red ball starting position
        # This only matters for passive mode
        self.objects["red_ball"].x = np.random.uniform(-4.5, 4.5)
        self.objects["red_ball"].y = np.random.uniform(-2, 4)
