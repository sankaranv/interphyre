from phyre2.level_builder import PHYRETemplate
from phyre2.objects import Ball, Basket, Platform
import numpy as np


class TouchBall(PHYRETemplate):
    def __init__(self):
        super().__init__()

    def build_task(self):
        self.name = "touch_ball"
        self.description = "Make the green ball touch the blue ball"

        # Set level properties
        self.target_object = "green_ball"
        self.goal_object = "blue_ball"
        self.action_objects = ["red_ball"]

        # Ball attributes are x, y, radius, color, dynamic
        # Set fixed attributes
        self.objects = {
            "green_ball": Ball(0, -4.9, 1, "green", True),
            "blue_ball": Ball(0.5, 0, 1, "blue", True),
            "red_ball": Ball(-3, 2.5, 0.45, "red", True),
        }

        task_ready = False

        while not task_ready:
            # Randomly sample green ball attributes
            self.objects["green_ball"].x = np.random.uniform(-4.5, 4.5)
            self.objects["green_ball"].radius = np.random.uniform(0.2, 0.34)

            # Sample blue ball attributes
            self.objects["blue_ball"].x = np.random.uniform(-4.5, 4.5)
            self.objects["blue_ball"].y = np.random.uniform(0.5, 4.5)
            self.objects["blue_ball"].radius = np.random.uniform(0.12, 0.6)

            # Ensure that the balls are not on top of each other so the level is not easy
            if np.abs(self.objects["green_ball"].x - self.objects["blue_ball"].x) > 0.5:
                task_ready = True
