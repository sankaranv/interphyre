from Box2D import b2ContactListener, b2_pi
from dataclasses import dataclass
import math
import numpy as np
import random


@dataclass
class Ball:
    x: float
    y: float
    radius: float
    color: str = "black"
    dynamic: bool = True


@dataclass
class Basket:
    x: float
    y: float
    scale: float
    color: str = "gray"
    dynamic: bool = False


@dataclass
class Platform:
    x: float
    y: float
    length: float
    angle: float
    color: str = "black"
    dynamic: bool = False


def set_seed(seed):
    np.random.seed(seed)
    random.seed(seed)


class GoalContactListener(b2ContactListener):
    def __init__(self, env):
        super(GoalContactListener, self).__init__()
        self.env = env
        self.target_object = env.level.target_object
        self.goal_object = env.level.goal_object

    def BeginContact(self, contact):
        fixture_a = contact.fixtureA
        fixture_b = contact.fixtureB
        # Access user data or other properties to identify specific objects
        if (
            fixture_a.body.userData == self.target_object
            and fixture_b.body.userData == self.goal_object
        ) or (
            fixture_a.body.userData == self.goal_object
            and fixture_b.body.userData == self.target_object
        ):
            # Player hit the target, terminate the episode
            self.env.done = True
            self.env.info["termination"] = "SUCCESS"
            self.env.success = True

    def EndContact(self, contact):
        pass


def create_collision_handler(env):
    # Attach the collision listener to the world
    contact_listener = GoalContactListener(env)
    env.world.contactListener = contact_listener


# Function to convert Box2D coordinates to Pygame screen coordinates
def b2_to_pygame(position, screen_width, screen_height, ppm=60):
    x, y = position
    x = int(x * ppm + screen_width / 2)  # Adjust the scaling factor as needed
    y = int(-y * ppm + screen_height / 2)  # Adjust the scaling factor as needed
    return x, y


def is_point_inside_polygon(x, y, polygon):
    """
    Check if a point (x, y) is inside a polygon.

    Parameters:
    - x, y: Coordinates of the point.
    - polygon: List of (x, y) coordinates representing the vertices of the polygon.

    Returns:
    - True if the point is inside the polygon, False otherwise.
    """
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if min(p1y, p2y) < y <= max(p1y, p2y) and x <= max(p1x, p2x):
            if p1y != p2y:
                xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                if p1x == p2x or x <= xinters:
                    inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def detect_stationary_world(world, level, tolerance=0.001):
    # Check if all objects are stationary
    for body in world.bodies:
        if body.userData in level.objects:
            if (
                body.linearVelocity.length > tolerance
                or body.angularVelocity > tolerance
            ):
                return False
    return True


def detect_success_basket(world, level, screen=None, tolerance=1):
    # Get the dimensions of the basket
    basket_height = 1.67 * level.objects["basket"].scale
    basket_width = 1.083 * level.objects["basket"].scale
    thickness = 0.075 * level.objects["basket"].scale
    angle_shift = math.cos(5 * b2_pi / 180) * 5

    # Get the target ball and basket from the world
    basket, target_object = None, None
    for body in world.bodies:
        if body.userData == level.target_object:
            target_object = body
        elif body.userData == "basket":
            basket = body
    if basket is None:
        raise Exception("Basket not found")
    if target_object is None:
        raise Exception("Target object not found")

    # Get basket and target positions
    target_position = target_object.position
    basket_position = basket.position
    target_radius = target_object.fixtures[0].shape.radius

    # Get the bounding box of the basket
    bottom_left = (
        basket_position[0]
        - basket_width / 2
        + thickness / 2
        + tolerance
        + target_radius,
        basket_position[1] + thickness / 2 + tolerance + target_radius,
    )
    bottom_right = (
        basket_position[0]
        + basket_width / 2
        - thickness / 2
        - tolerance
        - target_radius,
        basket_position[1] + thickness / 2 + tolerance + target_radius,
    )
    top_right = (
        basket_position[0]
        + basket_width / 2
        - thickness / 2
        + angle_shift
        - tolerance
        - target_radius,
        basket_position[1] + basket_height - thickness / 2 - tolerance - target_radius,
    )
    top_left = (
        basket_position[0]
        - basket_width / 2
        + thickness / 2
        - angle_shift
        + tolerance
        + target_radius,
        basket_position[1] + basket_height - thickness / 2 - tolerance - target_radius,
    )
    success_bounding_box = [bottom_left, bottom_right, top_right, top_left]

    if screen is not None:
        # Draw the bounding box
        import pygame

        screen_width, screen_height = screen.get_size()
        pygame.draw.polygon(
            screen,
            (255, 0, 0),
            [
                b2_to_pygame(v, screen_width, screen_height)
                for v in [bottom_left, bottom_right, top_right, top_left]
            ],
            1,
        )

    # Check if the current position of the target is inside the bounding box
    if is_point_inside_polygon(
        target_position[0], target_position[1], success_bounding_box
    ):
        return True

    return False
