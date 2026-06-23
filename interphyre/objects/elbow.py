import math

from Box2D import b2PolygonShape, b2World, b2_pi

from interphyre.config import PRECISION

from .base import InterphyreObject


class Elbow(InterphyreObject):
    """L-shaped object: two bars meeting at a corner.

    The body origin is placed at the corner point (x, y) and rotated by
    `angle` (direction of arm1 from horizontal). Arm2 extends from the same
    corner at `opening_angle` degrees CCW from arm1.

    Examples::

        # Right-angle L-bracket, arm1 pointing right, arm2 pointing up:
        Elbow(x=0, y=0, angle=0, opening_angle=90, arm1_length=2.0, arm2_length=1.5)

        # 120° open bracket rotated 45°:
        Elbow(x=1, y=1, angle=45, opening_angle=120, arm1_length=1.5, arm2_length=1.5)

    Attributes:
        angle: Direction of arm1 from horizontal in degrees (body rotation).
        opening_angle: Angle from arm1 to arm2 in degrees (CCW). Default 90.
        arm1_length: Length of first arm.
        arm2_length: Length of second arm (defaults to arm1_length if not given).
        thickness: Bar thickness (same for both arms).
    """

    def __init__(
        self,
        x: float,
        y: float,
        angle: float = 0.0,
        opening_angle: float = 90.0,
        arm1_length: float = 1.0,
        arm2_length: float | None = None,
        thickness: float = 0.2,
        **kwargs,
    ):
        super().__init__(x=x, y=y, angle=angle, **kwargs)
        self.opening_angle = opening_angle
        self.arm1_length = arm1_length
        self.arm2_length = arm2_length if arm2_length is not None else arm1_length
        self.thickness = thickness

    def _repr_dimensions(self) -> str:
        return (
            f"arm1={self.arm1_length:.2f}, arm2={self.arm2_length:.2f}, "
            f"opening={self.opening_angle:.1f}°, thickness={self.thickness:.2f}"
        )


def create_elbow(world: b2World, elbow: Elbow, name: str, use_ccd: bool = False):
    """Create a Box2D body for an Elbow object.

    The body origin is the corner. Arm1 points along the local +x axis; arm2
    points at opening_angle (CCW from +x). Both arms are full-length bars whose
    center lies at half their length along their respective directions.

    Args:
        world: The Box2D physics world.
        elbow: Elbow object with geometry parameters.
        name: Name assigned to body.userData.
        use_ccd: Enable bullet (continuous collision detection) mode.

    Returns:
        b2Body with two polygon fixtures.
    """
    x = round(float(elbow.x), PRECISION)
    y = round(float(elbow.y), PRECISION)
    body_angle = round(float(elbow.angle) * b2_pi / 180, PRECISION)
    opening_rad = round(float(elbow.opening_angle) * b2_pi / 180, PRECISION)
    arm1 = round(float(elbow.arm1_length), PRECISION)
    arm2 = round(float(elbow.arm2_length), PRECISION)
    half_thick = round(float(elbow.thickness) / 2, PRECISION)
    density = round(float(elbow.density), PRECISION)
    friction = round(float(elbow.friction), PRECISION)
    restitution = round(float(elbow.restitution), PRECISION)

    if elbow.dynamic:
        body = world.CreateDynamicBody(position=(x, y), angle=body_angle, bullet=use_ccd)
    else:
        body = world.CreateStaticBody(position=(x, y), angle=body_angle, bullet=use_ccd)

    # Arm1: extends along local +x axis; center at (arm1/2, 0).
    arm1_cx = round(arm1 / 2, PRECISION)
    arm1_shape = b2PolygonShape()
    arm1_shape.SetAsBox(round(arm1 / 2, PRECISION), half_thick, (arm1_cx, 0), 0)
    body.CreateFixture(shape=arm1_shape, density=density, friction=friction, restitution=restitution)

    # Arm2: extends at opening_angle from +x axis; center at (cos*arm2/2, sin*arm2/2).
    arm2_cx = round(math.cos(opening_rad) * arm2 / 2, PRECISION)
    arm2_cy = round(math.sin(opening_rad) * arm2 / 2, PRECISION)
    arm2_shape = b2PolygonShape()
    arm2_shape.SetAsBox(round(arm2 / 2, PRECISION), half_thick, (arm2_cx, arm2_cy), opening_rad)
    body.CreateFixture(shape=arm2_shape, density=density, friction=friction, restitution=restitution)

    body.userData = name
    return body
