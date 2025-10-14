from dataclasses import dataclass
from Box2D import b2World, b2PolygonShape, b2_pi
from .base import PhyreObject


@dataclass
class Basket(PhyreObject):
    """U-shaped container with configurable dimensions.

    The basket geometry is defined by bottom_width, top_width, and height.
    Use explicit dimensions for precise control, or the scale parameter for
    backwards compatibility with proportional sizing.

    Positioning uses an anchor system where (x, y) can refer to different
    reference points (e.g., bottom_center, center, top_center).

    Attributes:
        bottom_width (float): Interior width at the bottom of the basket
        top_width (float): Interior width at the top of the basket  
        height (float): Interior height of the basket
        scale (float): Proportional scaling factor (alternative to explicit dimensions)
        wall_thickness (float): Thickness of the basket walls (default: 0.175)
        floor_thickness (float): Thickness of the basket floor (default: wall_thickness)
        anchor (str): Reference point for positioning (default: "bottom_center")
        double_walls (bool): Whether to create anti-tunneling double walls (default: False)
        enable_sensor (bool): Whether to create a sensor for success detection (default: True)
        sensor_margin (float): Margin around the sensor area (default: 0.05)
        sensor_height_ratio (float): Height of sensor as ratio of basket height (default: 0.3)

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


def create_basket(world: b2World, basket: "Basket", name: str):
    """Create a Box2D physics body from a Basket object.
    
    The basket is built in local coordinates with bottom-center at origin,
    then positioned according to the basket's anchor point.

    Args:
        world (b2World): The Box2D physics world to create the basket in
        basket (Basket): The Basket object with geometry parameters
        name (str): Name to assign to the body's userData

    Returns:
        b2Body: Box2D body with basket fixtures
    """
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


