from Box2D import b2PolygonShape, b2World, b2_pi

from interphyre.config import PRECISION

from .base import InterphyreObject


class Bracket(InterphyreObject):
    """U-shaped object: a floor bar with two perpendicular walls, open at the top.

    Unlike Basket (trapezoidal, flared walls), Bracket has rectangular walls of
    uniform thickness — the interior is a clean rectangle. The body origin sits
    at the center of the floor bar's top surface; walls rise upward from each end.

    The entire bracket can be rotated by `angle`, making it usable as a sideways
    cage, an inverted tray, or any orientation in between.

    Examples::

        # Upright tray, 2 units wide, 1.5 units tall:
        Bracket(x=0, y=0, width=2.0, height=1.5, thickness=0.2)

        # Inverted tray (opening faces down):
        Bracket(x=0, y=2, angle=180, width=2.0, height=1.5, thickness=0.2)

        # Sideways cage (opening faces right):
        Bracket(x=0, y=0, angle=-90, width=2.0, height=1.5, thickness=0.2)

    Attributes:
        angle: Rotation of the whole bracket in degrees. 0 = opening faces up.
        width: Interior width between the inner wall surfaces.
        height: Interior height — length of each wall above the floor.
        thickness: Uniform thickness applied to the floor and both walls.
    """

    def __init__(
        self,
        x: float,
        y: float,
        angle: float = 0.0,
        width: float = 2.0,
        height: float = 1.5,
        thickness: float = 0.2,
        **kwargs,
    ):
        super().__init__(x=x, y=y, angle=angle, **kwargs)
        self.width = width
        self.height = height
        self.thickness = thickness

    def _repr_dimensions(self) -> str:
        return f"width={self.width:.2f}, height={self.height:.2f}, thickness={self.thickness:.2f}"

    @property
    def outer_width(self) -> float:
        """Total width including both wall thicknesses."""
        return self.width + 2 * self.thickness

    @property
    def outer_height(self) -> float:
        """Total height including floor thickness."""
        return self.height + self.thickness


def create_bracket(world: b2World, bracket: Bracket, name: str, use_ccd: bool = False):
    """Create a Box2D body for a Bracket object.

    The body origin sits at the center of the floor bar. Local coordinates:
    - Floor spans ±outer_width/2 in x, ±thickness/2 in y (centered at y=0).
    - Left wall at x = -(width/2 + thickness/2), from y=0 up to y=thickness+height.
    - Right wall at x = +(width/2 + thickness/2), from y=0 up to y=thickness+height.

    Args:
        world: The Box2D physics world.
        bracket: Bracket object with geometry parameters.
        name: Name assigned to body.userData.
        use_ccd: Enable bullet (continuous collision detection) mode.

    Returns:
        b2Body with three polygon fixtures (floor + two walls).
    """
    x = round(float(bracket.x), PRECISION)
    y = round(float(bracket.y), PRECISION)
    body_angle = round(float(bracket.angle) * b2_pi / 180, PRECISION)
    w = round(float(bracket.width), PRECISION)
    h = round(float(bracket.height), PRECISION)
    t = round(float(bracket.thickness), PRECISION)
    density = round(float(bracket.density), PRECISION)
    friction = round(float(bracket.friction), PRECISION)
    restitution = round(float(bracket.restitution), PRECISION)

    if bracket.dynamic:
        body = world.CreateDynamicBody(position=(x, y), angle=body_angle, bullet=use_ccd)
    else:
        body = world.CreateStaticBody(position=(x, y), angle=body_angle, bullet=use_ccd)

    # Floor: centered at local origin, full outer width.
    floor_half_w = round((w + 2 * t) / 2, PRECISION)
    floor_half_h = round(t / 2, PRECISION)
    floor_shape = b2PolygonShape()
    floor_shape.SetAsBox(floor_half_w, floor_half_h, (0, 0), 0)
    body.CreateFixture(shape=floor_shape, density=density, friction=friction, restitution=restitution)

    # Walls: rise from the top of the floor (local y = t/2) upward by height.
    wall_half_w = round(t / 2, PRECISION)
    wall_half_h = round(h / 2, PRECISION)
    # Wall centers sit at floor_top + h/2 = t/2 + h/2 above the floor center.
    wall_cy = round(t / 2 + h / 2, PRECISION)

    for sign in (-1, +1):
        wall_cx = round(sign * (w / 2 + t / 2), PRECISION)
        wall_shape = b2PolygonShape()
        wall_shape.SetAsBox(wall_half_w, wall_half_h, (wall_cx, wall_cy), 0)
        body.CreateFixture(shape=wall_shape, density=density, friction=friction, restitution=restitution)

    body.userData = name
    return body
