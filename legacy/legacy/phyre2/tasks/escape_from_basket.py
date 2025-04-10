from phyre2.level_builder import PHYRETemplate
from phyre2.objects import Ball, Basket, Platform
import numpy as np


class EscapeFromBasket(PHYRETemplate):
    def __init__(self):
        super().__init__()

    def build_task(self):
        self.name = "escape_from_basket"
        self.description = (
            "Get the green ball out of the basket and onto the purple wall"
        )

        # Set level properties
        self.target_object = "green_ball"
        self.goal_object = "purple_platform"
        self.action_objects = ["red_ball"]

        # Ball attributes are x, y, radius, color, dynamic
        # Platform attributes are x, y, length, angle, color, dynamic
        # Set fixed attributes
        self.objects = {
            "green_ball": Ball(0, -4.9, 0.4, "green", True),
            "red_ball": Ball(0, 0, 0.5, "red", True),
            "purple_platform": Platform(0, 0, 3, 90, "purple", False),
            "black_platform": Platform(-4, -4.5, 4, 75, "black", False),
            "basket": Basket(0, -4.9, 1.0, 0, "gray", True),
        }

        center_x = np.random.uniform(-1, 1)
        right_platform = Platform(0, 0, 7, 90, "purple", False)
        left_platform = Platform(0, 0, 7, 90, "black", False)

        # Set right platform such that the ends of the platform touch the ground and wall
        right_platform.angle = np.random.randint(10, 50)

        # Calculate x offset based on angle such that bottom of platform touches ground at center_x
        right_platform.x = (
            center_x
            + np.cos(right_platform.angle * np.pi / 180) * right_platform.length / 2
        )

        # Calculate y offset based on angle such that bottom of platform touches ground at center_x
        right_platform.y = (
            -5 + np.sin(right_platform.angle * np.pi / 180) * right_platform.length / 2
        )

        # Calculate x offset based on angle such that bottom of platform touches ground at center_x
        left_platform.angle = np.random.randint(-60, -30)
        left_platform.x = (
            center_x
            - np.cos(left_platform.angle * np.pi / 180) * left_platform.length / 2
        )
        left_platform.y = (
            -5 - np.sin(left_platform.angle * np.pi / 180) * left_platform.length / 2
        )

        # Choose whether left or right platform will be the target
        if np.random.uniform() < 0.5:
            left_platform.color = "purple"
            right_platform.color = "black"
            self.objects["purple_platform"] = left_platform
            self.objects["black_platform"] = right_platform
        else:
            left_platform.color = "black"
            right_platform.color = "purple"
            self.objects["purple_platform"] = right_platform
            self.objects["black_platform"] = left_platform

        # Set basket position towards the top of the black platform and parallel to it
        self.objects["basket"].angle = self.objects["black_platform"].angle
        if self.objects["black_platform"].angle < 0:
            self.objects["basket"].x = (
                self.objects["black_platform"].x
                - self.objects["black_platform"].length / 2
            )
        else:
            self.objects["basket"].x = (
                self.objects["black_platform"].x
                + self.objects["black_platform"].length / 2
            )
        self.objects["basket"].y = (
            self.objects["black_platform"].y + self.objects["black_platform"].length / 2
        )
        self.objects["basket"].x = np.clip(self.objects["basket"].x, -4.5, 4.5)

        # Put green ball inside basket
        if self.objects["purple_platform"].x < 0:
            self.objects["green_ball"].x = self.objects["basket"].x - 0.5
        else:
            self.objects["green_ball"].x = self.objects["basket"].x + 0.5
        self.objects["green_ball"].y = self.objects["basket"].y + 0.5

        # Randomly set red ball starting position
        # This only matters for passive mode
        self.objects["red_ball"].x = np.random.uniform(-4.5, 4.5)
        self.objects["red_ball"].y = np.random.uniform(-2, 4)
