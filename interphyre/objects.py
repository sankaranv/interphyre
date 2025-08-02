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
        **kwargs
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
    scale: float = 1.0


def create_basket(world: b2World, basket: Basket, name: str):

    angle_rad = basket.angle * b2_pi / 180
    width = round(1.083 * basket.scale, 2)
    height = round(1.67 * basket.scale, 2)
    theta = 5 * b2_pi / 180
    # Use square root scaling for more natural thickness progression
    base_thickness = 0.05
    thickness = round(base_thickness + 0.1 * math.sqrt(basket.scale), 2)
    angle_shift = math.cos(theta) * thickness

    body = (
        world.CreateDynamicBody(
            position=(basket.x, basket.y), angle=angle_rad, bullet=True
        )
        if basket.dynamic
        else world.CreateStaticBody(
            position=(basket.x, basket.y), angle=angle_rad, bullet=True
        )
    )

    # Bottom fixture - positioned at the base of the basket
    body.CreatePolygonFixture(
        box=(width / 2, thickness / 2),
        density=1,
        friction=basket.friction,
        restitution=basket.restitution,
    ).shape.SetAsBox(width / 2, thickness / 2, (0, 0), 0)

    # Left side fixture - properly aligned with bottom
    body.CreatePolygonFixture(
        box=(thickness / 2, height / 2),
        density=1,
        friction=basket.friction,
        restitution=basket.restitution,
    ).shape.SetAsBox(
        thickness / 2,
        height / 2 + thickness / 2,
        (-width / 2 + thickness / 2 - angle_shift, height / 2),
        theta,
    )

    # Right side fixture - properly aligned with bottom
    body.CreatePolygonFixture(
        box=(thickness / 2, height / 2),
        density=1,
        friction=basket.friction,
        restitution=basket.restitution,
    ).shape.SetAsBox(
        thickness / 2,
        height / 2 + thickness / 2,
        (width / 2 - thickness / 2 + angle_shift, height / 2),
        -theta,
    )

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
