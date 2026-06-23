from Box2D import b2PolygonShape, b2World, b2_pi

from interphyre.config import PRECISION

from .base import InterphyreObject


class Cross(InterphyreObject):
    """Two bars crossing at a shared center, forming an X or + shape.

    The body is placed at (x, y) and rotated by `angle`. Within that local
    frame, bar 1 sits at +spread degrees from the bisector axis and bar 2 at
    -spread degrees, so `angle` orients the whole cross and `spread` controls
    how open the X is.

    Examples::

        # Standard X (bars at 45° and 135°), bisector pointing up:
        Cross(x=0, y=0, angle=90, spread=45, arm_length=1.5, thickness=0.2)

        # Standingstick fan (narrow X, bisector pointing up):
        Cross(x=0, y=0, angle=90, spread=20, arm_length=2.0, thickness=0.15)

        # Plus-sign (bars horizontal and vertical):
        Cross(x=0, y=0, angle=0, spread=90, arm_length=1.0, thickness=0.2)

    Attributes:
        angle: Orientation of the bisector axis in degrees (body rotation).
        spread: Half-angle between each bar and the bisector in degrees. Default 45.
        arm_length: Distance from center to each tip. Total bar length = 2 * arm_length.
        thickness: Thickness of both bars.
    """

    def __init__(
        self,
        x: float,
        y: float,
        angle: float = 0.0,
        spread: float = 45.0,
        arm_length: float = 1.0,
        thickness: float = 0.2,
        **kwargs,
    ):
        super().__init__(x=x, y=y, angle=angle, **kwargs)
        self.spread = spread
        self.arm_length = arm_length
        self.thickness = thickness

    def _repr_dimensions(self) -> str:
        return f"arm_length={self.arm_length:.2f}, spread={self.spread:.1f}°, thickness={self.thickness:.2f}"


def create_cross(world: b2World, cross: Cross, name: str, use_ccd: bool = False):
    """Create a Box2D body for a Cross object.

    The body origin sits at the crossing point. Two rectangle fixtures are
    attached at ±spread from the body's local x-axis, giving each bar a full
    length of 2 * arm_length.

    Args:
        world: The Box2D physics world.
        cross: Cross object with geometry parameters.
        name: Name assigned to body.userData.
        use_ccd: Enable bullet (continuous collision detection) mode.

    Returns:
        b2Body with two polygon fixtures.
    """
    x = round(float(cross.x), PRECISION)
    y = round(float(cross.y), PRECISION)
    body_angle = round(float(cross.angle) * b2_pi / 180, PRECISION)
    spread_rad = round(float(cross.spread) * b2_pi / 180, PRECISION)
    arm = round(float(cross.arm_length), PRECISION)
    half_thick = round(float(cross.thickness) / 2, PRECISION)
    density = round(float(cross.density), PRECISION)
    friction = round(float(cross.friction), PRECISION)
    restitution = round(float(cross.restitution), PRECISION)

    if cross.dynamic:
        body = world.CreateDynamicBody(position=(x, y), angle=body_angle, bullet=use_ccd)
    else:
        body = world.CreateStaticBody(position=(x, y), angle=body_angle, bullet=use_ccd)

    # Two bars centered at the body origin, each rotated ±spread from the bisector.
    for local_angle in (spread_rad, -spread_rad):
        shape = b2PolygonShape()
        shape.SetAsBox(arm, half_thick, (0, 0), round(local_angle, PRECISION))
        body.CreateFixture(shape=shape, density=density, friction=friction, restitution=restitution)

    body.userData = name
    return body
