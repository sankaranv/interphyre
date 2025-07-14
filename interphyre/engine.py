from Box2D import b2World, b2ContactListener, b2Contact, b2_pi
from typing import Any, Dict, List, Tuple, Optional, Union
from interphyre.level import Level
from interphyre.objects import (
    Ball,
    Bar,
    Basket,
    PhyreObject,
    create_basket,
    create_ball,
    create_bar,
    create_walls,
)
from interphyre.config import SimulationConfig, PerformanceProfiler
import math


class GoalContactListener(b2ContactListener):
    def __init__(
        self,
        track_all_contacts: bool = True,
        track_relevant_only: bool = False,
        profiler: Optional[PerformanceProfiler] = None,
        relevant_pairs: Optional[set] = None,
    ):
        super().__init__()
        self.track_all_contacts = track_all_contacts
        self.track_relevant_only = track_relevant_only
        self.profiler = profiler
        self.relevant_pairs = relevant_pairs or set()

        # Use tuples instead of frozensets for faster lookups
        self.contacts = set()
        self.contact_duration = {}
        self.contact_start_time = {}
        self.current_time = 0

        # Research logging
        self.all_contacts_log = []
        self.contact_events = []  # For detailed research

    def BeginContact(self, contact: b2Contact):
        a = contact.fixtureA.body.userData
        b = contact.fixtureB.body.userData
        if a and b:
            # Use frozenset for consistent contact pair representation
            contact_pair = frozenset((a, b))

            # Check if we should track this contact
            should_track = (
                self.track_all_contacts
                or not self.track_relevant_only
                or contact_pair in self.relevant_pairs
            )

            if should_track:
                self.contacts.add(contact_pair)
                self.contact_start_time[contact_pair] = self.current_time

            # Only log if profiling is enabled (performance optimization)
            if self.track_all_contacts and self.profiler:
                self.contact_events.append(
                    {
                        "time": self.current_time,
                        "event": "begin",
                        "pair": contact_pair,
                        "objects": (a, b),
                    }
                )

    def EndContact(self, contact: b2Contact):
        a = contact.fixtureA.body.userData
        b = contact.fixtureB.body.userData
        if a and b:
            contact_pair = frozenset((a, b))

            # Check if we should track this contact
            should_track = (
                self.track_all_contacts
                or not self.track_relevant_only
                or contact_pair in self.relevant_pairs
            )

            if should_track:
                self.contacts.discard(contact_pair)
                # Reset the contact start time when contact ends
                if contact_pair in self.contact_start_time:
                    del self.contact_start_time[contact_pair]

            # Only log if profiling is enabled (performance optimization)
            if self.track_all_contacts and self.profiler:
                self.contact_events.append(
                    {
                        "time": self.current_time,
                        "event": "end",
                        "pair": contact_pair,
                        "objects": (a, b),
                    }
                )

    def Update(self, dt):
        """Update the current time."""
        self.current_time += dt

    def GetContactDuration(self, a, b):
        """Get the current unbroken contact duration between objects a and b."""
        contact_pair = frozenset((a, b))
        if contact_pair in self.contacts and contact_pair in self.contact_start_time:
            return self.current_time - self.contact_start_time[contact_pair]
        return 0

    def IsInContactForDuration(self, a, b, required_duration):
        """Check if objects a and b are currently in unbroken contact for at least the required duration."""
        contact_pair = frozenset((a, b))
        if contact_pair in self.contacts and contact_pair in self.contact_start_time:
            current_duration = self.current_time - self.contact_start_time[contact_pair]
            return current_duration >= required_duration
        return False

    def get_contact_log(self):
        """Get the full contact event log for research purposes."""
        return self.contact_events.copy()

    def get_contact_statistics(self):
        """Get statistics about all contacts for research purposes."""
        # Only calculate statistics if profiling is enabled (performance optimization)
        if not self.profiler or not self.contact_events:
            return {
                "total_events": 0,
                "unique_pairs": 0,
                "pair_counts": {},
                "current_contacts": len(self.contacts),
            }

        # Count contact events by object pairs
        pair_counts = {}
        for event in self.contact_events:
            pair = event["pair"]
            if pair not in pair_counts:
                pair_counts[pair] = {"begins": 0, "ends": 0}
            pair_counts[pair][event["event"] + "s"] += 1

        return {
            "total_events": len(self.contact_events),
            "unique_pairs": len(pair_counts),
            "pair_counts": pair_counts,
            "current_contacts": len(self.contacts),
        }

    def ClearContacts(self):
        """Clear all contacts and durations."""
        self.contacts = set()
        self.contact_start_time = {}


class Box2DEngine:
    def __init__(
        self, level: Optional[Level] = None, config: Optional[SimulationConfig] = None
    ):
        self.config = config or SimulationConfig()
        self.profiler = PerformanceProfiler(self.config.enable_profiling)

        self.world = b2World(gravity=self.config.gravity, doSleep=self.config.do_sleep)
        self.contact_listener = GoalContactListener(
            track_all_contacts=self.config.track_all_contacts,
            track_relevant_only=self.config.track_relevant_contacts_only,
            profiler=self.profiler,
        )
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
            # Update relevant contact pairs based on level
            self._update_relevant_contacts()

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
            elif isinstance(obj, Bar):
                body = create_bar(self.world, obj, name)
            elif isinstance(obj, Basket):
                body = create_basket(self.world, obj, name)
            else:
                raise ValueError(f"Unknown object type for '{name}': {type(obj)}")
            self.bodies[name] = body

    def _update_relevant_contacts(self):
        """Update the list of relevant contact pairs based on the level's success condition."""
        if self.level is None:
            return

        # Only track contacts that are likely to be relevant for success conditions
        # This reduces memory usage and processing overhead
        relevant_pairs = set()

        # Track contacts between action objects and other objects
        for action_obj in self.level.action_objects:
            for obj_name in self.level.objects.keys():
                if obj_name != action_obj:
                    pair = frozenset((action_obj, obj_name))
                    relevant_pairs.add(pair)

        # Also track contacts between green objects and other objects (common success targets)
        for obj_name in self.level.objects.keys():
            if "green" in obj_name.lower():
                for other_obj in self.level.objects.keys():
                    if other_obj != obj_name:
                        pair = frozenset((obj_name, other_obj))
                        relevant_pairs.add(pair)

        self.contact_listener.relevant_pairs = relevant_pairs

    def place_action_objects(
        self,
        positions: List[Tuple[Union[int, float], Union[int, float], Union[int, float]]],
    ):
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
            # Update object's position and size with the provided tuple
            if isinstance(obj, Ball):
                x, y, size = pos
                obj.x, obj.y, obj.radius = x, y, size
                body = create_ball(self.world, obj, name)
            elif isinstance(obj, Bar):
                x, y, _ = pos
                obj.x, obj.y = x, y
                body = create_bar(self.world, obj, name)
            elif isinstance(obj, Basket):
                x, y, _ = pos
                obj.x, obj.y = x, y
                body = create_basket(self.world, obj, name)
            else:
                raise ValueError(f"Unknown object type for '{name}': {type(obj)}")
            self.bodies[name] = body

    def get_state(self) -> Dict[str, Any]:
        """
        Return the current simulation state.

        Returns:
            Dictionary containing the current physics state including:
            - object positions, velocities, angles, and angular velocities
            - contact information
            - world properties
        """
        if self.world is None or self.level is None:
            return {}

        state = {
            "objects": {},
            "contacts": {},
            "world_properties": {
                "gravity": self.world.gravity,
                "body_count": self.world.bodyCount,
                "contact_count": self.world.contactCount,
            },
        }

        # Get object states
        for name, obj in self.level.objects.items():
            if name in self.bodies:
                body = self.bodies[name]
                state["objects"][name] = {
                    "position": (body.position.x, body.position.y),
                    "velocity": (body.linearVelocity.x, body.linearVelocity.y),
                    "angle": body.angle,
                    "angular_velocity": body.angularVelocity,
                    "type": type(obj).__name__,
                    "dynamic": body.type == 2,  # b2_dynamicBody
                }
            else:
                # Object not yet placed (e.g., action objects)
                state["objects"][name] = {
                    "position": (obj.x, obj.y),
                    "velocity": (0.0, 0.0),
                    "angle": obj.angle,
                    "angular_velocity": 0.0,
                    "type": type(obj).__name__,
                    "dynamic": obj.dynamic,
                }

        # Get contact information
        for contact_pair in self.contact_listener.contacts:
            obj1, obj2 = contact_pair
            state["contacts"][f"{obj1}_{obj2}"] = {
                "objects": contact_pair,
                "duration": self.contact_listener.GetContactDuration(obj1, obj2),
            }

        return state

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
        contact_pair = frozenset((name1, name2))
        return contact_pair in self.contact_listener.contacts

    def world_is_stationary(self) -> bool:
        # TODO: this logic is buggy, we need a time based check
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
                    body.linearVelocity.length > self.config.stationary_tolerance
                    or body.angularVelocity > self.config.stationary_tolerance
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

    def is_in_basket(
        self, basket_name: str, target_name: str, tolerance: float = 0.001
    ) -> List[Tuple[float, float]]:

        if self.level is None or self.world is None:
            raise ValueError("Level or world not initialized.")
        if basket_name not in self.level.objects:
            raise ValueError(f"{basket_name} not found in level objects.")
        basket = self.level.objects[basket_name]
        if not isinstance(basket, Basket):
            raise ValueError(f"{basket_name} is not a basket.")

        basket_height = 1.67 * basket.scale
        basket_width = 1.083 * basket.scale
        thickness = 0.075 * basket.scale
        angle_shift = math.cos(5 * b2_pi / 180) * 5

        if target_name not in self.level.objects:
            raise ValueError(f"{target_name} not found in level objects.")
        target = self.level.objects[target_name]
        if not isinstance(target, Ball):
            raise ValueError(
                f"{target_name} is a {type(target)}, is_in_basket currently only works with Balls."
            )

        bottom_left = (
            basket.x - basket_width / 2 + thickness / 2 + tolerance + target.radius,
            basket.y + thickness / 2 + tolerance + target.radius,
        )
        bottom_right = (
            basket.x + basket_width / 2 - thickness / 2 - tolerance - target.radius,
            basket.y + thickness / 2 + tolerance + target.radius,
        )
        top_right = (
            basket.x
            + basket_width / 2
            - thickness / 2
            + angle_shift
            - tolerance
            - target.radius,
            basket.y + basket_height - thickness / 2 - tolerance - target.radius,
        )
        top_left = (
            basket.x
            - basket_width / 2
            + thickness / 2
            - angle_shift
            + tolerance
            + target.radius,
            basket.y + basket_height - thickness / 2 - tolerance - target.radius,
        )
        success_bounding_box = [bottom_left, bottom_right, top_right, top_left]
        return success_bounding_box

    def is_in_basket_sensor(self, basket_name: str, target_name: str) -> bool:
        """
        Check if a ball is inside a basket using the sensor fixture.
        This is an alternative to the original is_in_basket method that uses
        point-in-polygon testing.

        Args:
            basket_name: Name of the basket object
            target_name: Name of the ball object

        Returns:
            bool: True if the ball is inside the basket, False otherwise
        """
        if self.level is None or self.world is None:
            raise ValueError("Level or world not initialized.")
        if basket_name not in self.level.objects:
            raise ValueError(f"{basket_name} not found in level objects.")
        basket = self.level.objects[basket_name]
        if not isinstance(basket, Basket):
            raise ValueError(f"{basket_name} is not a basket.")

        if target_name not in self.level.objects:
            raise ValueError(f"{target_name} not found in level objects.")
        target = self.level.objects[target_name]
        if not isinstance(target, Ball):
            raise ValueError(
                f"{target_name} is a {type(target)}, is_in_basket_sensor currently only works with Balls."
            )

        # Get the basket and target bodies from the world
        basket_body = None
        target_body = None
        for body in self.world.bodies:
            if body.userData == basket_name:
                basket_body = body
            elif body.userData == target_name:
                target_body = body

        if basket_body is None or target_body is None:
            return False

        # Check if the target is in contact with the basket's sensor fixture
        for contact in self.world.contacts:
            # Check if this contact involves our basket and target
            if (
                contact.fixtureA.body == basket_body
                and contact.fixtureB.body == target_body
            ) or (
                contact.fixtureA.body == target_body
                and contact.fixtureB.body == basket_body
            ):
                # Check if one of the fixtures is a sensor (our basket's interior)
                if contact.fixtureA.sensor or contact.fixtureB.sensor:
                    return True

        return False

    def is_in_contact_for_duration(self, a, b, success_time: Optional[float] = None):
        """Check if objects are currently in unbroken contact for the required duration."""
        if success_time is None:
            success_time = self.config.default_success_time
        return self.contact_listener.IsInContactForDuration(a, b, success_time)

    def time_update(self, dt):
        self.contact_listener.Update(dt)

    def get_contact_duration(self, a, b):
        return self.contact_listener.GetContactDuration(a, b)

    def get_contact_log(self):
        """Get the full contact event log for research purposes."""
        return self.contact_listener.get_contact_log()

    def get_contact_statistics(self):
        """Get statistics about all contacts for research purposes."""
        return self.contact_listener.get_contact_statistics()
