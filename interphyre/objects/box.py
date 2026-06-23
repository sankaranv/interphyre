from Box2D import b2World, b2_pi

from interphyre.config import PRECISION

from .base import InterphyreObject


class Box(InterphyreObject):
    """A solid filled rectangle.

    Unlike Bar (which is a thin rod parameterised by length and thickness),
    Box is parameterised by explicit width and height — the two dimensions
    are treated symmetrically. Useful for tables, platforms, walls, struts,
    and any solid block where "length vs thickness" is not a natural
    distinction.

    The body origin sits at the geometric center. Positive ``angle`` rotates
    the box counter-clockwise.

    Initialization patterns::

        # Center + dimensions
        Box(x=0, y=-3, width=4.0, height=1.0)

        # Bounding box corners (horizontal box flush with the floor)
        Box(left=-5, right=0, top=-3, bottom=-5)

        # Dynamic falling block
        Box(x=1, y=3, width=0.5, height=0.5, dynamic=True)

    Attributes:
        width: Horizontal extent of the box.
        height: Vertical extent of the box.
        left, right, top, bottom: Bounding-box edges (read-only derived
            properties for axis-aligned boxes; meaningful only when angle=0).
    """

    def __init__(
        self,
        x=None,
        y=None,
        width=None,
        height=None,
        left=None,
        right=None,
        top=None,
        bottom=None,
        angle: float = 0.0,
        **kwargs,
    ):
        if (
            left is not None
            and right is not None
            and top is not None
            and bottom is not None
        ):
            x = (left + right) / 2
            y = (top + bottom) / 2
            width = right - left
            height = top - bottom
        elif x is not None and y is not None and width is not None and height is not None:
            pass
        else:
            raise ValueError(
                "Box requires either (left, right, top, bottom) "
                "or (x, y, width, height)"
            )
        if width <= 0 or height <= 0:
            raise ValueError(f"Box width and height must be positive: {width=}, {height=}")
        super().__init__(x=x, y=y, angle=angle, **kwargs)
        self.width = width
        self.height = height

    def _repr_dimensions(self) -> str:
        return f"width={self.width:.2f}, height={self.height:.2f}"

    @property
    def left(self) -> float:
        return self.x - self.width / 2

    @property
    def right(self) -> float:
        return self.x + self.width / 2

    @property
    def top(self) -> float:
        return self.y + self.height / 2

    @property
    def bottom(self) -> float:
        return self.y - self.height / 2


def create_box(world: b2World, box: "Box", name: str, use_ccd: bool = False):
    """Create a Box2D physics body from a Box object.

    Args:
        world: The Box2D physics world.
        box: Box object with geometry and physical properties.
        name: Unique identifier stored as body.userData.
        use_ccd: Enable continuous collision detection (bullet mode).

    Returns:
        b2Body with a single rectangle polygon fixture.
    """
    x = round(float(box.x), PRECISION)
    y = round(float(box.y), PRECISION)
    angle = round(float(box.angle) * b2_pi / 180, PRECISION)
    half_w = round(float(box.width) / 2, PRECISION)
    half_h = round(float(box.height) / 2, PRECISION)
    density = round(float(box.density), PRECISION)
    friction = round(float(box.friction), PRECISION)
    restitution = round(float(box.restitution), PRECISION)
    linear_damping = round(float(box.linear_damping), PRECISION)
    angular_damping = round(float(box.angular_damping), PRECISION)

    if box.dynamic:
        body = world.CreateDynamicBody(position=(x, y), angle=angle, bullet=use_ccd)
    else:
        body = world.CreateStaticBody(position=(x, y), angle=angle)

    body.CreatePolygonFixture(
        box=(half_w, half_h),
        density=density,
        friction=friction,
        restitution=restitution,
    )
    body.linearDamping = linear_damping
    body.angularDamping = angular_damping
    body.userData = name
    return body
