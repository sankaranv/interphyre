import math

from Box2D import b2PolygonShape, b2World

from interphyre.config import PRECISION

from .base import InterphyreObject


class Wedge(InterphyreObject):
    """A filled trapezoidal or triangular solid wedge.

    Distinct from a Bar-based ramp (a thin inclined surface): a Wedge is a
    solid convex polygon — a thick block whose top surface slopes. It is the
    natural representation for large corner-filling slope shapes like those
    used in the PHYRE Virtual Tools task set.

    In world coordinates the four corners are::

        (x1, y1)  ----------  (x2, y2)   ← sloped top surface
           |                       |
        (x1, bottom) -------- (x2, bottom)  ← floor edge

    When ``y1 == bottom`` or ``y2 == bottom`` the shape degenerates to a
    right triangle and the degenerate vertex is omitted, leaving three
    corners.

    The body origin is placed at the bounding-box center:
    ``x = (x1 + x2) / 2``, ``y = (bottom + max(y1, y2)) / 2``.

    Usage examples::

        # Classic left-rising slope (fills lower-left corner of scene)
        Wedge(x1=-5, y1=3.0, x2=1.0, y2=0.5, bottom=-5)

        # Mirrored right-rising slope (fills lower-right corner)
        Wedge(x1=-1.0, y1=0.5, x2=5, y2=3.0, bottom=-5)

        # Right triangle (right edge at floor — purely triangular)
        Wedge(x1=-5, y1=3.0, x2=1.0, y2=-5, bottom=-5)

        # Elevated trapezoid (e.g. a strut resting on a table)
        Wedge(x1=1.0, y1=2.0, x2=3.0, y2=2.0, bottom=0.5)

    Attributes:
        x1: X-coordinate of the left edge.
        y1: Y-coordinate of the top of the left edge.
        x2: X-coordinate of the right edge.
        y2: Y-coordinate of the top of the right edge.
        bottom: Y-coordinate shared by both bottom corners.
        width: Horizontal extent ``x2 - x1`` (read-only).
        slope_angle: Angle of the top surface in degrees (read-only).
    """

    def __init__(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        bottom: float = -5.0,
        **kwargs,
    ):
        if x2 <= x1:
            raise ValueError(f"Wedge requires x2 > x1, got x1={x1}, x2={x2}")
        if y1 < bottom or y2 < bottom:
            raise ValueError(
                f"Wedge top heights must be >= bottom: y1={y1}, y2={y2}, bottom={bottom}"
            )
        cx = (x1 + x2) / 2
        cy = (bottom + max(y1, y2)) / 2
        # angle is not used for Wedge — shape is fully encoded in the vertices.
        super().__init__(x=cx, y=cy, angle=0.0, **kwargs)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.bottom = bottom

    def _repr_dimensions(self) -> str:
        return (
            f"x1={self.x1:.2f}, y1={self.y1:.2f}, "
            f"x2={self.x2:.2f}, y2={self.y2:.2f}, bottom={self.bottom:.2f}"
        )

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def slope_angle(self) -> float:
        return math.degrees(math.atan2(self.y2 - self.y1, self.x2 - self.x1))


def create_wedge(world: b2World, wedge: "Wedge", name: str, use_ccd: bool = False):
    """Create a Box2D physics body from a Wedge object.

    Vertices are computed in the body's local frame (relative to body center).
    Degenerate corners (where a top height equals ``bottom``) are omitted so
    the fixture is always a valid convex polygon.

    Args:
        world: The Box2D physics world.
        wedge: Wedge object with geometry and physical properties.
        name: Unique identifier stored as body.userData.
        use_ccd: Enable continuous collision detection (bullet mode).

    Returns:
        b2Body with a single convex polygon fixture.
    """
    cx = round(float(wedge.x), PRECISION)
    cy = round(float(wedge.y), PRECISION)
    density = round(float(wedge.density), PRECISION)
    friction = round(float(wedge.friction), PRECISION)
    restitution = round(float(wedge.restitution), PRECISION)
    linear_damping = round(float(wedge.linear_damping), PRECISION)
    angular_damping = round(float(wedge.angular_damping), PRECISION)

    x1 = float(wedge.x1)
    y1 = float(wedge.y1)
    x2 = float(wedge.x2)
    y2 = float(wedge.y2)
    bot = float(wedge.bottom)

    # Build vertices in CCW order, skipping degenerate corners.
    verts = [(x1 - cx, bot - cy)]  # bottom-left always present
    if abs(y1 - bot) > 1e-9:
        verts.append((x1 - cx, y1 - cy))  # top-left (omit for right triangle)
    if abs(y2 - bot) > 1e-9:
        verts.append((x2 - cx, y2 - cy))  # top-right (omit for right triangle)
    verts.append((x2 - cx, bot - cy))  # bottom-right always present

    verts = [(round(v[0], PRECISION), round(v[1], PRECISION)) for v in verts]

    if wedge.dynamic:
        body = world.CreateDynamicBody(position=(cx, cy), angle=0.0, bullet=use_ccd)
    else:
        body = world.CreateStaticBody(position=(cx, cy), angle=0.0)

    shape = b2PolygonShape(vertices=verts)
    body.CreateFixture(
        shape=shape,
        density=density,
        friction=friction,
        restitution=restitution,
    )
    body.linearDamping = linear_damping
    body.angularDamping = angular_damping
    body.userData = name
    return body
