from phyre2.level_builder import PHYRETemplate
from phyre2.objects import Ball, Basket, Platform
import numpy as np


class BallHitWall(PHYRETemplate):
    def __init__(self):
        super().__init__()

    def build_task(self):
        self.name = "ball_hit_wall"
        self.description = "Make the green ball hit the left or right wall"

        # Set level properties
        self.target_object = "green_ball"
        self.goal_object = "purple_platform"
        self.action_objects = ["red_ball"]

        # Ball attributes are x, y, radius, color, dynamic
        # Platform attributes are x, y, length, angle, color, dynamic
        # Set fixed attributes
        self.objects = {
            "green_ball": Ball(0, -4.9, 1, "green", True),
            "red_ball": Ball(0, 0, 0.5, "red", True),
            "purple_platform": Platform(0, 0, 5, 90, "purple", False),
            "left_platform": Platform(-4, -4.5, 0.55, 75, "black", False),
            "right_platform": Platform(4, -4.5, 0.55, 105, "black", False),
            "base_platform": Platform(0, -4, 3.95, 0, "black", False),
        }

        # Randomly set purple platform to be the left or right wall
        self.objects["purple_platform"].x = np.random.choice([-4.9, 4.9])

        # Randomly set green ball starting position
        self.objects["green_ball"].x = np.random.uniform(-4.5, 4.5)
        self.objects["green_ball"].y = np.random.uniform(-4.5, 1)
        self.objects["green_ball"].radius = np.random.uniform(0.2, 0.45)

        # Randomly set red ball starting position
        # This only matters for passive mode
        self.objects["red_ball"].x = np.random.uniform(-4.5, 4.5)
        self.objects["red_ball"].y = np.random.uniform(-2, 4)
