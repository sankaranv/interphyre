from dataclasses import dataclass, field
from typing import Tuple
from Box2D import b2PolygonShape, b2World, b2_pi, b2Vec2
import math


@dataclass
class PhyreObject:
    x: float
    y: float
    angle: float = 0.0  # in degrees
    color: str = "black"
    dynamic: bool = True
    restitution: float = 0.5
    friction: float = 0.5


@dataclass
class Ball(PhyreObject):
    radius: float = 0.5


class Bar(PhyreObject):
    def __init__(
        self,
        x=None,
        y=None,
        length=2.0,
        angle=0.0,
        thickness=0.2,
        x1=None,
        y1=None,
        x2=None,
        y2=None,
        left=None,
        right=None,
        top=None,
        bottom=None,
        **kwargs,
    ):
        # Handle different initialization patterns
        if x1 is not None and y1 is not None and x2 is not None and y2 is not None:
            # Initialize from endpoints
            x = (x1 + x2) / 2
            y = (y1 + y2) / 2
            length = math.hypot(x2 - x1, y2 - y1)
            angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        elif left is not None and right is not None and y is not None:
            # Initialize from left/right
            x = (left + right) / 2
            length = right - left
            angle = 0.0
        elif top is not None and bottom is not None and x is not None:
            # Initialize from top/bottom
            y = (top + bottom) / 2
            length = top - bottom
            angle = 90.0
        elif x is None or y is None:
            raise ValueError(
                "Must provide either (x,y) or endpoints or left/right or top/bottom"
            )

        # Initialize private attributes first
        self._x = x
        self._y = y
        self._angle = angle
        self._length = length
        self._thickness = thickness

        # Call parent constructor with the same values
        super().__init__(x=x, y=y, angle=angle, **kwargs)

        # Update endpoints after everything is initialized
        self._update_endpoints()

    def _update_endpoints(self):
        """Update endpoint coordinates based on center, length, and angle"""
        angle_rad = math.radians(self._angle)
        dx = (self._length / 2) * math.cos(angle_rad)
        dy = (self._length / 2) * math.sin(angle_rad)
        self._x1 = self._x - dx
        self._y1 = self._y - dy
        self._x2 = self._x + dx
        self._y2 = self._y + dy

    def _update_center_from_endpoints(self):
        """Update center, length, and angle from endpoints"""
        self._x = (self._x1 + self._x2) / 2
        self._y = (self._y1 + self._y2) / 2
        self._length = math.hypot(self._x2 - self._x1, self._y2 - self._y1)
        self._angle = math.degrees(math.atan2(self._y2 - self._y1, self._x2 - self._x1))

    # Endpoint properties
    @property
    def x1(self):
        return self._x1

    @property
    def y1(self):
        return self._y1

    @property
    def x2(self):
        return self._x2

    @property
    def y2(self):
        return self._y2

    @x1.setter
    def x1(self, value):
        self._x1 = value
        self._update_center_from_endpoints()

    @y1.setter
    def y1(self, value):
        self._y1 = value
        self._update_center_from_endpoints()

    @x2.setter
    def x2(self, value):
        self._x2 = value
        self._update_center_from_endpoints()

    @y2.setter
    def y2(self, value):
        self._y2 = value
        self._update_center_from_endpoints()

    # Bounding box properties (read-only for convenience)
    @property
    def left(self):
        return min(self._x1, self._x2)

    @property
    def right(self):
        return max(self._x1, self._x2)

    @property
    def top(self):
        return max(self._y1, self._y2)

    @property
    def bottom(self):
        return min(self._y1, self._y2)

    # Override properties to update endpoints when changed
    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self._update_endpoints()

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self._update_endpoints()

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value
        self._update_endpoints()

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, value):
        self._length = value
        self._update_endpoints()

    @property
    def thickness(self):
        return self._thickness

    @thickness.setter
    def thickness(self, value):
        self._thickness = value


@dataclass
class Basket(PhyreObject):
    """U-shaped container with configurable dimensions.

    The basket geometry is defined by bottom_width, top_width, and height.
    Use explicit dimensions for precise control, or the scale parameter for
    backwards compatibility with proportional sizing.

    Positioning uses an anchor system where (x, y) can refer to different
    reference points (e.g., bottom_center, center, top_center).

    Examples:
        # Explicit dimensions
        basket = Basket(x=0, y=-3, bottom_width=2.0, top_width=2.4, height=2.5)

        # Using scale (backwards compatible)
        basket = Basket(x=0, y=-3, scale=1.5)

        # Using convenience method
        basket = Basket.from_width_and_flare(x=0, y=-3, bottom_width=2.0, flare_ratio=1.2)
    """

    bottom_width: float = None
    top_width: float = None
    height: float = None
    scale: float = None
    wall_thickness: float = 0.175
    floor_thickness: float = None
    anchor: str = "bottom_center"
    double_walls: bool = False
    segmented_walls: bool = False
    enable_sensor: bool = True
    sensor_margin: float = 0.05
    sensor_height_ratio: float = 0.3

    def __post_init__(self):
        """Initialize dimensions from scale or apply defaults."""
        if self.floor_thickness is None:
            self.floor_thickness = self.wall_thickness

        if self.scale is not None:
            if self.bottom_width is None:
                self.bottom_width = 1.083 * self.scale
            if self.top_width is None:
                self.top_width = 1.083 * self.scale * 1.25
            if self.height is None:
                self.height = 1.67 * self.scale
        else:
            if self.bottom_width is None:
                self.bottom_width = 2.0
            if self.top_width is None:
                self.top_width = 2.2
            if self.height is None:
                self.height = 3.0

    @classmethod
    def from_width_and_flare(
        cls, x, y, bottom_width, flare_ratio=1.2, height=None, **kwargs
    ):
        """Create basket from bottom width and flare ratio.

        Args:
            x: X-coordinate
            y: Y-coordinate
            bottom_width: Interior width at bottom
            flare_ratio: Ratio of top_width to bottom_width (default 1.2)
            height: Interior height (defaults to bottom_width * 1.5)
            **kwargs: Additional Basket parameters
        """
        top_width = bottom_width * flare_ratio
        if height is None:
            height = bottom_width * 1.5
        return cls(
            x=x,
            y=y,
            bottom_width=bottom_width,
            top_width=top_width,
            height=height,
            **kwargs,
        )

    @property
    def interior_bottom_width(self):
        return self.bottom_width

    @property
    def interior_top_width(self):
        return self.top_width

    @property
    def interior_height(self):
        return self.height

    @property
    def total_width(self):
        return self.bottom_width + 2 * self.wall_thickness

    @property
    def total_height(self):
        return self.height + self.floor_thickness

    def get_anchor_offset(self):
        """Get offset from bottom-center to the specified anchor point."""
        if self.anchor == "bottom_center":
            return (0, 0)
        elif self.anchor == "center":
            return (0, -self.height / 2)
        elif self.anchor == "top_center":
            return (0, -self.height)
        elif self.anchor == "bottom_left":
            return (self.bottom_width / 2, 0)
        elif self.anchor == "bottom_right":
            return (-self.bottom_width / 2, 0)
        elif self.anchor == "top_left":
            return (self.top_width / 2, -self.height)
        elif self.anchor == "top_right":
            return (-self.top_width / 2, -self.height)
        else:
            raise ValueError(f"Unknown anchor: {self.anchor}")


def create_basket(world: b2World, basket: Basket, name: str):
    """Create a basket body with U-shaped geometry.

    The basket is built in local coordinates with bottom-center at origin,
    then positioned according to the basket's anchor point.

    Args:
        world: Box2D world to create the basket in
        basket: Basket object with geometry parameters
        name: Name to assign to the body's userData

    Returns:
        Box2D body with basket fixtures
    """
    from Box2D import b2PolygonShape

    angle_rad = basket.angle * b2_pi / 180
    bw = basket.bottom_width
    tw = basket.top_width
    h = basket.height
    wt = basket.wall_thickness
    ft = basket.floor_thickness
    anchor_offset_x, anchor_offset_y = basket.get_anchor_offset()

    if basket.dynamic:
        body = world.CreateDynamicBody(
            position=(basket.x, basket.y), angle=angle_rad, bullet=True
        )
    else:
        body = world.CreateStaticBody(
            position=(basket.x, basket.y), angle=angle_rad, bullet=True
        )

    # Floor
    floor_shape = b2PolygonShape()
    floor_shape.SetAsBox(
        (bw + 2 * wt) / 2,
        ft / 2,
        (anchor_offset_x, anchor_offset_y + ft / 2),
        0,
    )
    body.CreateFixture(
        shape=floor_shape,
        density=1,
        friction=basket.friction,
        restitution=basket.restitution,
    )

    # Left wall (trapezoid)
    left_wall_vertices = [
        (-bw / 2 - wt + anchor_offset_x, ft + anchor_offset_y),
        (-tw / 2 - wt + anchor_offset_x, ft + h + anchor_offset_y),
        (-tw / 2 + anchor_offset_x, ft + h + anchor_offset_y),
        (-bw / 2 + anchor_offset_x, ft + anchor_offset_y),
    ]
    left_wall_shape = b2PolygonShape(vertices=left_wall_vertices)
    body.CreateFixture(
        shape=left_wall_shape,
        density=1,
        friction=basket.friction,
        restitution=basket.restitution,
    )

    # Right wall (trapezoid)
    right_wall_vertices = [
        (bw / 2 + wt + anchor_offset_x, ft + anchor_offset_y),
        (bw / 2 + anchor_offset_x, ft + anchor_offset_y),
        (tw / 2 + anchor_offset_x, ft + h + anchor_offset_y),
        (tw / 2 + wt + anchor_offset_x, ft + h + anchor_offset_y),
    ]
    right_wall_shape = b2PolygonShape(vertices=right_wall_vertices)
    body.CreateFixture(
        shape=right_wall_shape,
        density=1,
        friction=basket.friction,
        restitution=basket.restitution,
    )

    # Optional double walls for anti-tunneling
    if basket.double_walls:
        inner_gap = 0.03
        left_inner_vertices = [
            (-bw / 2 + inner_gap + anchor_offset_x, ft + anchor_offset_y),
            (-tw / 2 + inner_gap + anchor_offset_x, ft + h + anchor_offset_y),
            (-tw / 2 + inner_gap + wt / 2 + anchor_offset_x, ft + h + anchor_offset_y),
            (-bw / 2 + inner_gap + wt / 2 + anchor_offset_x, ft + anchor_offset_y),
        ]
        left_inner_shape = b2PolygonShape(vertices=left_inner_vertices)
        body.CreateFixture(
            shape=left_inner_shape,
            density=0.1,
            friction=basket.friction,
            restitution=basket.restitution,
        )

        right_inner_vertices = [
            (bw / 2 - inner_gap + anchor_offset_x, ft + anchor_offset_y),
            (bw / 2 - inner_gap - wt / 2 + anchor_offset_x, ft + anchor_offset_y),
            (tw / 2 - inner_gap - wt / 2 + anchor_offset_x, ft + h + anchor_offset_y),
            (tw / 2 - inner_gap + anchor_offset_x, ft + h + anchor_offset_y),
        ]
        right_inner_shape = b2PolygonShape(vertices=right_inner_vertices)
        body.CreateFixture(
            shape=right_inner_shape,
            density=0.1,
            friction=basket.friction,
            restitution=basket.restitution,
        )

    # Optional sensor fixture for success detection
    if basket.enable_sensor:
        sensor_height = h * basket.sensor_height_ratio
        sensor_width = bw - 2 * basket.sensor_margin
        sensor_center_y = ft + sensor_height / 2

        sensor_shape = b2PolygonShape()
        sensor_shape.SetAsBox(
            sensor_width / 2,
            sensor_height / 2,
            (anchor_offset_x, anchor_offset_y + sensor_center_y),
            0,
        )
        sensor_fixture = body.CreateFixture(
            shape=sensor_shape,
            density=0,
            isSensor=True,
        )
        sensor_fixture.userData = f"{name}_sensor"

    body.userData = name
    return body


def create_walls(
    world: b2World, wall_thickness: float, room_width: float, room_height: float
):

    left_wall = world.CreateStaticBody(
        position=(-room_width / 2 + wall_thickness / 2, 0),
        shapes=b2PolygonShape(box=(wall_thickness, room_height)),
    )
    right_wall = world.CreateStaticBody(
        position=(room_width / 2 - wall_thickness / 2, 0),
        shapes=b2PolygonShape(box=(wall_thickness, room_height)),
    )
    top_wall = world.CreateStaticBody(
        position=(0, room_height / 2 - wall_thickness / 2),
        shapes=b2PolygonShape(box=(room_width, wall_thickness)),
    )
    bottom_wall = world.CreateStaticBody(
        position=(0, -room_height / 2 + wall_thickness / 2),
        shapes=b2PolygonShape(box=(room_width, wall_thickness)),
    )

    left_wall.userData = "left_wall"
    right_wall.userData = "right_wall"
    top_wall.userData = "top_wall"
    bottom_wall.userData = "bottom_wall"
    return left_wall, right_wall, top_wall, bottom_wall


def create_ball(world: b2World, ball: Ball, name: str):

    body = (
        world.CreateDynamicBody(
            position=b2Vec2(float(ball.x), float(ball.y)),
            angle=0,
            fixedRotation=False,
            bullet=True,
        )
        if ball.dynamic
        else world.CreateStaticBody(
            position=b2Vec2(float(ball.x), float(ball.y)),
            angle=0,
            fixedRotation=False,
            bullet=True,
        )
    )
    body.CreateCircleFixture(
        radius=ball.radius,
        density=1,
        friction=ball.friction,
        restitution=ball.restitution,
    )
    body.userData = name
    return body


def create_bar(world: b2World, bar: Bar, name: str):

    angle = bar.angle * b2_pi / 180
    body = (
        world.CreateDynamicBody(
            position=(bar.x, bar.y),
            angle=angle,
            bullet=True,
        )
        if bar.dynamic
        else world.CreateStaticBody(position=(bar.x, bar.y), angle=angle)
    )
    body.CreatePolygonFixture(
        box=(bar.length / 2, bar.thickness / 2),
        density=1,
        friction=bar.friction,
        restitution=bar.restitution,
    )
    body.userData = name
    return body
