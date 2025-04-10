import numpy as np
from phyre2.objects import Ball, PhyreObject
from phyre2.level import Level
from typing import cast
from phyre2.levels import register_level


def success_condition(engine):
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", 3)


def build_level(seed=None):
    rng = np.random.default_rng(seed)

    green_ball_radius = rng.uniform(0.2, 0.7)
    blue_ball_radius = rng.uniform(0.2, 0.8)
    red_ball_radius = rng.uniform(0.4, 1)
    green_ball = Ball(
        x=rng.uniform(-5 + green_ball_radius, 5 - green_ball_radius),
        y=rng.uniform(-3, 4.5),
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )
    blue_ball = Ball(
        x=rng.uniform(-5 + blue_ball_radius, 5 - blue_ball_radius),
        y=rng.uniform(0.5, 4.5),
        radius=blue_ball_radius,
        color="blue",
        dynamic=True,
    )
    red_ball = Ball(
        x=-3,
        y=2.5,
        radius=red_ball_radius,
        color="red",
        dynamic=True,
    )

    # Avoid trivial solutions
    while abs(green_ball.x - blue_ball.x) < (green_ball.radius + blue_ball.radius):
        green_ball.x = rng.uniform(-4.5, 4.5)
        blue_ball.x = rng.uniform(-4.5, 4.5)

    objects = {
        "green_ball": green_ball,
        "blue_ball": blue_ball,
        "red_ball": red_ball,
    }

    return Level(
        name="pinhole_jar",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball"},
    )


register_level("pinhole_jar")(build_level)
