from phyre2.level_builder import PHYRETemplate
from phyre2.objects import Ball, Basket, Platform
import numpy as np


class BalanceBeam(PHYRETemplate):
    def __init__(self):
        super().__init__()

    def build_task(self):
        self.name = "balance_beam"
        self.description = "The green ball should not fall off the balance beam"

        # Set level properties
        self.target_object = "green_ball"
        self.goal_object = "blue_platform"
        self.action_objects = ["red_ball"]

        # Ball attributes are x, y, radius, color, dynamic
        # Platform attributes are x, y, length, angle, color, dynamic
        # Basket attributes are x, y, scale, color, dynamic
        # Set fixed attributes

        # Randomly set red ball starting position
        # This only matters for passive mode
        self.objects["red_ball"].x = np.random.uniform(-4.5, 4.5)
        self.objects["red_ball"].y = np.random.uniform(-2, 4)
