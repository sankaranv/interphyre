from dataclasses import dataclass
from Box2D import b2World, b2Vec2
from .base import PhyreObject


@dataclass
class Ball(PhyreObject):
    radius: float = 0.5


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


