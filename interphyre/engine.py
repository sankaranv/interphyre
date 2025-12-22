from Box2D import b2World, b2ContactListener, b2Contact, b2_pi
from typing import Any, Dict, List, Tuple, Optional, Union
import math
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


class GoalContactListener(b2ContactListener):
    """Contact listener for tracking object collisions and success conditions.

    This listener monitors all contact events in the physics world and tracks
    which objects are in contact with each other. It supports both performance-
    optimized tracking (relevant contacts only) and comprehensive research logging.

    Attributes:
        track_all_contacts (bool): Whether to track all contact events
        track_relevant_only (bool): Whether to only track relevant contact pairs
        profiler (Optional[PerformanceProfiler]): Performance profiler for timing
        relevant_pairs (set): Set of contact pairs to track for performance
        contacts (set): Currently active contact pairs
        contact_duration (dict): Duration of each contact pair
        contact_start_time (dict): Start time of each contact
        current_time (float): Current simulation time
        all_contacts_log (list): Complete log of all contact events
        contact_events (list): Detailed list of contact events
    """

    def __init__(
        self,
        track_all_contacts: bool = True,
        track_relevant_only: bool = False,
        profiler: Optional[PerformanceProfiler] = None,
        relevant_pairs: Optional[set] = None,
    ):
        """Initialize the contact listener.

        Args:
            track_all_contacts: Whether to track all contact events (default: True)
            track_relevant_only: Whether to only track relevant pairs for performance (default: False)
            profiler: Performance profiler for timing analysis (default: None)
            relevant_pairs: Set of contact pairs to track for performance (default: None)
        """
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

        # Logging
        self.all_contacts_log = []
        self.contact_events = []

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

            # Only log if profiling is enabled
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

            # Only log if profiling is enabled
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
        """Update the internal simulation time counter.

        Args:
            dt: Time delta in seconds to add to the current simulation time.
        """
        self.current_time += dt

    def GetContactDuration(self, a, b):
        """Get the current unbroken contact duration between two objects.

        Args:
            a: Name of the first object
            b: Name of the second object

        Returns:
            float: Duration in seconds that objects have been in continuous contact.
                  Returns 0 if objects are not currently in contact.
        """
        contact_pair = frozenset((a, b))
        if contact_pair in self.contacts and contact_pair in self.contact_start_time:
            return self.current_time - self.contact_start_time[contact_pair]
        return 0

    def IsInContactForDuration(self, a, b, required_duration):
        """Check if objects are currently in unbroken contact for at least the required duration.

        Args:
            a: Name of the first object
            b: Name of the second object
            required_duration: Minimum contact duration in seconds

        Returns:
            bool: True if objects are in contact and have been for at least required_duration seconds.
        """
        contact_pair = frozenset((a, b))

        # First check: Are they in the contact tracking set?
        if (
            contact_pair not in self.contacts
            or contact_pair not in self.contact_start_time
        ):
            return False

        # Check duration
        current_duration = self.current_time - self.contact_start_time[contact_pair]
        return current_duration >= required_duration

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
        """Clear all contact tracking data and reset the simulation time.

        Removes all active contacts, contact start times, and resets the internal
        time counter to zero. Used when resetting the simulation or loading a new level.
        """
        self.contacts = set()
        self.contact_start_time = {}
        self.current_time = 0.0


class Box2DEngine:
    """Main physics engine for the Interphyre simulation.

    This engine manages the Box2D physics world, object creation, contact tracking,
    and simulation stepping. It provides the core physics simulation functionality
    for the Interphyre environment.

    Attributes:
        config (SimulationConfig): Configuration parameters for the simulation
        profiler (PerformanceProfiler): Performance profiler for timing analysis
        world (b2World): The Box2D physics world
        contact_listener (GoalContactListener): Contact listener for collision tracking
        level (Optional[Level]): Current level being simulated
        bodies (Dict[str, b2Body]): Dictionary mapping object names to Box2D bodies
    """

    def __init__(
        self, level: Optional[Level] = None, config: Optional[SimulationConfig] = None
    ):
        """Initialize the physics engine.

        Args:
            level: Initial level to load (default: None)
            config: Simulation configuration parameters (default: SimulationConfig())
        """
        self.config = config or SimulationConfig()
        self.profiler = PerformanceProfiler(self.config.enable_profiling)

        self.world = b2World(gravity=self.config.gravity, doSleep=self.config.do_sleep)
        self.world.warmStarting = self.config.warm_starting
        self.world.subStepping = self.config.substepping
        self.world.continuousPhysics = self.config.continuous_physics

        self.contact_listener = GoalContactListener(
            track_all_contacts=self.config.track_all_contacts,
            track_relevant_only=self.config.track_relevant_contacts_only,
            profiler=self.profiler,
        )
        self.world.contactListener = self.contact_listener
        self.reset(level)

    def reset(self, level: Optional[Level] = None):
        """Reset the engine with a new level.

        Clears the current physics world and loads a new level. This destroys
        all existing bodies and creates new ones based on the level definition.

        Args:
            level: New level to load (default: None, clears the world)
        """
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

        # Create objects in a deterministic order to ensure reproducibility
        for name in sorted(level.objects.keys()):

            obj = level.objects[name]
            # Skip placement of the action object
            if name in level.action_objects:
                continue
            if isinstance(obj, Ball):
                assert (
                    self.world is not None
                ), "World is not initialized. Call reset() before placing objects."
                body = create_ball(
                    self.world,
                    obj,
                    name,
                    use_ccd=self.config.continuous_collision_detection,
                )
            elif isinstance(obj, Bar):
                body = create_bar(
                    self.world,
                    obj,
                    name,
                    use_ccd=self.config.continuous_collision_detection,
                )
            elif isinstance(obj, Basket):
                body = create_basket(
                    self.world,
                    obj,
                    name,
                    use_ccd=self.config.continuous_collision_detection,
                )
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
        """Place action objects at the start of the simulation.

        Args:
            positions: List of (x, y, size) tuples for each action object.
                For bars and baskets, size is ignored but must be provided.

        Note:
            All position and size values are rounded to 8 decimal places to ensure determinism.
        """
        if self.level is None:
            raise ValueError(
                "The level is not set. Please call reset() with a valid level before placing action objects."
            )
        assert (
            self.world is not None
        ), "World is not initialized. Call reset() before placing objects."

        PRECISION = 8
        for name, pos in zip(self.level.action_objects, positions):
            obj = self.level.objects[name]
            if isinstance(obj, Ball):
                x, y, size = pos
                obj.x = round(float(x), PRECISION)
                obj.y = round(float(y), PRECISION)
                obj.radius = round(float(size), PRECISION)
                body = create_ball(
                    self.world,
                    obj,
                    name,
                    use_ccd=self.config.continuous_collision_detection,
                )
            elif isinstance(obj, Bar):
                x, y, _ = pos
                obj.x = round(float(x), PRECISION)
                obj.y = round(float(y), PRECISION)
                body = create_bar(
                    self.world,
                    obj,
                    name,
                    use_ccd=self.config.continuous_collision_detection,
                )
            elif isinstance(obj, Basket):
                x, y, _ = pos
                obj.x = round(float(x), PRECISION)
                obj.y = round(float(y), PRECISION)
                body = create_basket(
                    self.world,
                    obj,
                    name,
                    use_ccd=self.config.continuous_collision_detection,
                )
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

    def is_in_basket(self, basket_name: str, target_name: str) -> bool:
        """
        Check if a ball is inside a basket using the sensor fixture.

        Args:
            basket_name: Name of the basket object
            target_name: Name of the ball object

        Returns:
            bool: True if the ball is inside the basket, False otherwise
        """
        if self.level is None or self.world is None:
            raise ValueError("Level or world not initialized.")
        if (
            target_name not in self.level.objects
            or basket_name not in self.level.objects
        ):
            return False
        basket = self.level.objects[basket_name]
        if not isinstance(basket, Basket):
            raise ValueError(f"{basket_name} is not a basket.")
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

    def _distance_ball_to_bar(self, ball_pos, bar_obj):
        """Calculate the distance from a ball's center to the closest point on a bar's surface.

        Args:
            ball_pos: Ball position (x, y) as a tuple or object with .x and .y attributes
            bar_obj: Bar object with x, y, angle, length, thickness attributes

        Returns:
            float: Distance from ball center to bar surface
        """
        # Transform ball center into bar's local coordinate system
        angle_rad = math.radians(-bar_obj.angle)  # negative for inverse rotation
        dx = ball_pos.x - bar_obj.x
        dy = ball_pos.y - bar_obj.y
        local_x = dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
        local_y = dx * math.sin(angle_rad) + dy * math.cos(angle_rad)

        half_length = bar_obj.length / 2
        half_thickness = bar_obj.thickness / 2

        # Clamp local_x and local_y to the rectangle bounds
        closest_x = max(-half_length, min(half_length, local_x))
        closest_y = max(-half_thickness, min(half_thickness, local_y))

        # Compute distance from ball center to closest point on rectangle
        dist = math.sqrt((local_x - closest_x) ** 2 + (local_y - closest_y) ** 2)
        return dist

    def is_in_contact_for_duration(self, a, b, success_time: Optional[float] = None):
        """Check if objects are currently in unbroken contact for the required duration.

        Args:
            a: Name of the first object
            b: Name of the second object
            success_time: Required contact duration in seconds. If None, uses config.default_success_time.

        Returns:
            bool: True if objects are in contact and have been for at least success_time seconds.

        Raises:
            ValueError: If level is not set or objects are not in the level.
        """
        if self.level is None:
            raise ValueError(
                "Level is not set. Please call reset() with a valid level before checking for contact duration."
            )
        if a not in self.level.objects or b not in self.level.objects:
            return False
        if success_time is None:
            success_time = self.config.default_success_time

        # Validate physical contact by checking object positions
        # This ensures objects are actually touching, not just registered in the contact tracking system
        if self.config.validate_contact_distance:
            body_a = self.bodies.get(a)
            body_b = self.bodies.get(b)
            if body_a is None or body_b is None:
                return False

            # Get object sizes to determine contact threshold
            obj_a = self.level.objects[a]
            obj_b = self.level.objects[b]

            # Calculate actual distance and contact threshold based on object types
            distance = None
            contact_threshold = None

            if isinstance(obj_a, Ball) and isinstance(obj_b, Ball):
                # Ball-ball contact: distance is center-to-center
                pos_a = body_a.position
                pos_b = body_b.position
                distance = ((pos_a.x - pos_b.x) ** 2 + (pos_a.y - pos_b.y) ** 2) ** 0.5
                contact_threshold = (
                    obj_a.radius + obj_b.radius + 0.01
                )  # Small tolerance for floating point
            elif isinstance(obj_a, Ball) and isinstance(obj_b, Bar):
                # Ball-bar contact: calculate distance from ball center to bar surface
                distance = self._distance_ball_to_bar(body_a.position, obj_b)
                contact_threshold = obj_a.radius + 0.01  # Ball radius plus tolerance
            elif isinstance(obj_a, Bar) and isinstance(obj_b, Ball):
                # Bar-ball contact: same as ball-bar (symmetric)
                distance = self._distance_ball_to_bar(body_b.position, obj_a)
                contact_threshold = obj_b.radius + 0.01  # Ball radius plus tolerance
            else:
                # For other object combinations (bar-bar, basket, etc.), use center-to-center
                # with a conservative threshold
                pos_a = body_a.position
                pos_b = body_b.position
                distance = ((pos_a.x - pos_b.x) ** 2 + (pos_a.y - pos_b.y) ** 2) ** 0.5
                contact_threshold = 0.1  # Conservative threshold

            # If objects are too far apart, they cannot be in contact
            # Clear the contact tracking entry to keep state consistent
            if distance is not None and distance > contact_threshold:
                contact_pair = frozenset((a, b))
                self.contact_listener.contacts.discard(contact_pair)
                if contact_pair in self.contact_listener.contact_start_time:
                    del self.contact_listener.contact_start_time[contact_pair]
                return False

        # Objects are in contact (validated if enabled) - check if duration requirement is met
        return self.contact_listener.IsInContactForDuration(a, b, success_time)

    def time_update(self, dt):
        """Update the contact listener's internal time tracking.

        Args:
            dt: Time delta in seconds to add to the current simulation time.
        """
        self.contact_listener.Update(dt)

    def get_contact_duration(self, a, b):
        """Get the current unbroken contact duration between two objects.

        Args:
            a: Name of the first object
            b: Name of the second object

        Returns:
            float: Duration in seconds that objects have been in continuous contact.
                  Returns 0 if objects are not currently in contact.

        Raises:
            ValueError: If level is not set or objects are not in the level.
        """
        if self.level is None:
            raise ValueError(
                "Level is not set. Please call reset() with a valid level before checking for contact duration."
            )
        if a not in self.level.objects or b not in self.level.objects:
            return 0
        return self.contact_listener.GetContactDuration(a, b)

    def get_contact_log(self):
        """Get the full contact event log for research purposes."""
        return self.contact_listener.get_contact_log()

    def get_contact_statistics(self):
        """Get statistics about all contacts for research purposes."""
        return self.contact_listener.get_contact_statistics()
