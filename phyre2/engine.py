from Box2D import b2World, b2ContactListener, b2Contact, b2_pi
from typing import Any, Dict, List, Tuple, Optional
from phyre2.level import Level
from phyre2.objects import (
    Ball,
    Platform,
    Basket,
    PhyreObject,
    create_basket,
    create_ball,
    create_platform,
    create_walls,
)
import math


class GoalContactListener(b2ContactListener):
    def __init__(self):
        super().__init__()
        self.contacts = set()

    def BeginContact(self, contact: b2Contact):
        # Retrieve userData that we stored under the name
        a = contact.fixtureA.body.userData
        b = contact.fixtureB.body.userData
        if a and b:
            # Using frozenset ensures order-independence
            self.contacts.add(frozenset((a, b)))

    def EndContact(self, contact: b2Contact):
        a = contact.fixtureA.body.userData
        b = contact.fixtureB.body.userData
        if a and b:
            self.contacts.discard(frozenset((a, b)))

    def ClearContacts(self):
        """Clear all contacts."""
        self.contacts = set()


class Box2DEngine:
    def __init__(self, level: Optional[Level] = None):

        self.tolerance: float = 0.001
        self.world = b2World(gravity=(0, -10), doSleep=True)
        self.contact_listener = GoalContactListener()
        self.world.contactListener = self.contact_listener
        self.reset(level)

    def reset(self, level: Optional[Level] = None):
        """Reset the engine with a new level."""
        self.world.ClearForces()
        for body in self.world.bodies:
            self.world.DestroyBody(body)
        self.level = level
        self.contact_listener.ClearContacts()
        self.bodies = {}
        if level is not None:
            self._create_world(level)

    def _create_world(self, level):

        # Create walls on the edges of the screen
        left_wall, right_wall, top_wall, bottom_wall = create_walls(
            self.world, 0.01, 10, 10
        )
        self.bodies["left_wall"] = left_wall
        self.bodies["right_wall"] = right_wall
        self.bodies["top_wall"] = top_wall
        self.bodies["bottom_wall"] = bottom_wall

        for name, obj in level.objects.items():
            # Skip placement of the action object
            if name in level.action_objects:
                continue
            if isinstance(obj, Ball):
                assert (
                    self.world is not None
                ), "World is not initialized. Call reset() before placing objects."
                body = create_ball(self.world, obj, name)
            elif isinstance(obj, Platform):
                body = create_platform(self.world, obj, name)
            elif isinstance(obj, Basket):
                body = create_basket(self.world, obj, name)
            else:
                raise ValueError(f"Unknown object type for '{name}': {type(obj)}")
            self.bodies[name] = body

    def place_action_objects(self, positions: List[Tuple[float, float]]):
        """Place the action objects once, at the start of the simulation."""
        if self.level is None:
            raise ValueError(
                "The level is not set. Please call reset() with a valid level before placing action objects."
            )
        assert (
            self.world is not None
        ), "World is not initialized. Call reset() before placing objects."
        for name, pos in zip(self.level.action_objects, positions):
            obj = self.level.objects[name]
            # Update object's position with the provided tuple
            obj.x, obj.y = pos
            if isinstance(obj, Ball):
                body = create_ball(self.world, obj, name)
            elif isinstance(obj, Platform):
                body = create_platform(self.world, obj, name)
            elif isinstance(obj, Basket):
                body = create_basket(self.world, obj, name)
            else:
                raise ValueError(f"Unknown object type for '{name}': {type(obj)}")
            self.bodies[name] = body

    def get_state(self):
        """
        Return the current simulation state.
        This is a stub – in practice you might render the scene to an image,
        return raw physics data, or process the state as needed.
        """
        return {}

    def objects(self) -> Dict[str, PhyreObject]:
        if self.level is None:
            raise ValueError(
                "The level is not set. Please call reset() with a valid level before accessing objects."
            )
        return self.level.objects

    def has_contact(self, name1: str, name2: str) -> bool:
        """
        Check if the two object names have come into contact.
        """
        return frozenset((name1, name2)) in self.contact_listener.contacts

    def detect_stationary_world(self) -> bool:
        if self.world is None:
            raise ValueError(
                "World is not initialized. Call reset() before checking for stationary bodies."
            )
        if self.level is None:
            raise ValueError(
                "Level is not set. Please call reset() before checking for stationary bodies."
            )
        for body in self.world.bodies:
            if body.userData in self.level.objects:
                if (
                    body.linearVelocity.length > self.tolerance
                    or body.angularVelocity > self.tolerance
                ):
                    return False
        return True

    def _is_point_inside_polygon(
        self, x: float, y: float, polygon: List[Tuple[float, float]]
    ) -> bool:
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

    def detect_success_basket(self, tolerance: float = 1, screen=None) -> bool:
        if self.level is None or self.world is None:
            raise ValueError("Level or world not initialized.")
        basket_obj = self.level.objects.get("basket")
        if not basket_obj:
            raise Exception("Basket not found in level objects.")
        if not isinstance(basket_obj, Basket):
            raise Exception("Object is not a basket.")
        basket_height = 1.67 * basket_obj.scale
        basket_width = 1.083 * basket_obj.scale
        thickness = 0.075 * basket_obj.scale
        angle_shift = math.cos(5 * b2_pi / 180) * 5
        basket_body, target_body = None, None
        for body in self.world.bodies:
            if body.userData == self.level.target_object:
                target_body = body
            elif body.userData == "basket":
                basket_body = body
        if basket_body is None:
            raise Exception("Basket not found in world bodies.")
        if target_body is None:
            raise Exception("Target object not found in world bodies.")
        target_position = target_body.position
        basket_position = basket_body.position
        target_radius = target_body.fixtures[0].shape.radius

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
            basket_position[1]
            + basket_height
            - thickness / 2
            - tolerance
            - target_radius,
        )
        top_left = (
            basket_position[0]
            - basket_width / 2
            + thickness / 2
            - angle_shift
            + tolerance
            + target_radius,
            basket_position[1]
            + basket_height
            - thickness / 2
            - tolerance
            - target_radius,
        )
        success_bounding_box = [bottom_left, bottom_right, top_right, top_left]
        return self._is_point_inside_polygon(
            target_position[0], target_position[1], success_bounding_box
        )
