from dataclasses import dataclass
from Box2D import b2World, b2Vec2
from .base import PhyreObject


@dataclass
class Ball(PhyreObject):
    """A circular physics object.

    Represents a ball or sphere in the physics simulation. Balls can be
    dynamic (affected by gravity and collisions) or static (fixed in place).

    Attributes:
        radius (float): Radius of the ball in simulation units (default: 0.5)

    Examples:
        # Create a dynamic red ball
        ball = Ball(x=0, y=5, radius=1.0, color="red")

        # Create a static platform ball
        platform = Ball(x=0, y=-3, radius=2.0, dynamic=False, color="gray")
    """

    radius: float = 0.5


def create_ball(world: b2World, ball: Ball, name: str):
    """Create a Box2D physics body from a Ball object.

    Converts a Ball data object into a Box2D physics body that can be
    simulated in the physics world.

    Args:
        world (b2World): The Box2D physics world to create the body in
        ball (Ball): The Ball object containing position and physical properties
        name (str): Unique identifier for the physics body

    Returns:
        b2Body: The created Box2D physics body

    Note:
        The body is created with bullet=True for continuous collision detection
        to prevent fast-moving objects from tunneling through other objects.
    """

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
        density=ball.density,
        friction=ball.friction,
        restitution=ball.restitution,
    )

    body.linearDamping = ball.linear_damping
    body.angularDamping = ball.angular_damping
    body.userData = name
    return body
