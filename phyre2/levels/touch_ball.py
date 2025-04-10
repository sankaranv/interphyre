import numpy as np
from phyre2.objects import Ball, PhyreObject
from phyre2.level import Level
from typing import cast
from phyre2.levels import register_level


def success_condition(engine):
    return engine.has_contact("green_ball", "blue_ball")


def build_level(seed=None):
    rng = np.random.default_rng(seed)

    green_ball = Ball(
        x=rng.uniform(-4.5, 4.5),
        y=-4.9,
        radius=rng.uniform(0.2, 0.34),
        color="green",
        dynamic=True,
    )
    blue_ball = Ball(
        x=rng.uniform(-4.5, 4.5),
        y=rng.uniform(0.5, 4.5),
        radius=rng.uniform(0.12, 0.6),
        color="blue",
        dynamic=True,
    )
    red_ball = Ball(
        x=-3,
        y=2.5,
        radius=0.45,
        color="red",
        dynamic=True,
    )

    # Avoid trivial solutions
    while abs(green_ball.x - blue_ball.x) < 0.5:
        green_ball.x = rng.uniform(-4.5, 4.5)
        blue_ball.x = rng.uniform(-4.5, 4.5)

    objects = {
        "green_ball": green_ball,
        "blue_ball": blue_ball,
        "red_ball": red_ball,
    }

    return Level(
        name="touch_ball",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        target_object="green_ball",
        goal_object="blue_ball",
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball"},
    )


register_level("touch_ball")(build_level)
