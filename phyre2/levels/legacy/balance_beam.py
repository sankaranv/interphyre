import numpy as np
from typing import cast
from phyre2.objects import Ball, Platform, Basket, PhyreObject
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):
    # Success: the green ball remains on the blue platform for at least 3 seconds.
    return engine.is_in_contact_for_duration("green_ball", "blue_platform", 3)


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    # Create the green ball (target)
    green_ball = Ball(
        x=0.0,
        y=5.0,
        radius=0.5,
        color="green",
        dynamic=True,
    )

    # Create the blue platform (balance beam, goal)
    blue_platform = Platform(
        x=0.0,
        y=4.9,
        length=4.0,
        angle=0.0,
        color="blue",
        dynamic=False,
    )

    # Create the red ball (action object)
    red_ball = Ball(
        x=0.0,
        y=0.0,
        radius=0.4,
        color="red",
        dynamic=True,
    )

    # Randomly set the red ball starting position (this only matters in passive mode).
    red_ball.x = rng.uniform(-4.5, 4.5)
    red_ball.y = rng.uniform(-2, 4)

    # Assemble the objects dictionary.
    objects = {
        "green_ball": green_ball,
        "blue_platform": blue_platform,
        "red_ball": red_ball,
    }

    return Level(
        name="balance_beam",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        target_object="green_ball",
        goal_object="blue_platform",
        success_condition=success_condition,
        metadata={"description": "The green ball should not fall off the balance beam"},
    )


register_level("balance_beam")(build_level)
