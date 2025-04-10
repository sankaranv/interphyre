import numpy as np
from typing import cast
from phyre2.objects import Ball, Platform, Basket, PhyreObject
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):
    # Success when the green_ball contacts the purple_platform.
    return engine.has_contact("green_ball", "purple_platform")


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    # Create fixed objects with base values.
    green_ball = Ball(
        x=0.0,
        y=4.9,
        radius=1.0,  # will be randomized below
        color="green",
        dynamic=True,
    )
    red_ball = Ball(
        x=0.0,
        y=0.0,
        radius=0.4,
        color="red",
        dynamic=True,
    )
    left_funnel_platform = Platform(
        x=-3.0,
        y=0.0,  # to be randomized
        length=2.65,
        angle=-25.0,
        color="black",
        dynamic=False,
    )
    right_funnel_platform = Platform(
        x=3.0,
        y=0.0,  # to be randomized, same as left_funnel_platform
        length=2.65,
        angle=25.0,
        color="black",
        dynamic=False,
    )
    black_platform = Platform(
        x=0.0,
        y=-4.8,
        length=1.0,
        angle=0.0,
        color="black",
        dynamic=False,
    )
    purple_platform = Platform(
        x=0.0,
        y=-4.95,
        length=1.0,
        angle=0.0,
        color="purple",
        dynamic=False,
    )
    ground_platform = Platform(
        x=0.0,
        y=-4.95,
        length=4.0,
        angle=0.0,
        color="black",
        dynamic=False,
    )

    # Assemble the objects dictionary.
    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "left_funnel_platform": left_funnel_platform,
        "right_funnel_platform": right_funnel_platform,
        "black_platform": black_platform,
        "purple_platform": purple_platform,
        "ground_platform": ground_platform,
    }

    # Randomly set the funnel (beam) height.
    new_y = rng.uniform(1.5, 3)
    left_funnel_platform.y = new_y
    right_funnel_platform.y = new_y

    # Randomly set green ball attributes.
    green_ball.radius = rng.uniform(0.2, 0.3)
    green_ball.x = rng.uniform(-0.5, 0.5)

    # Set purple_platform starting position (simulate a funnel target pad).
    purple_platform.x = rng.choice([-4.0, 4.0])
    ground_platform.x = -np.sign(purple_platform.x)
    black_platform.x = np.sign(purple_platform.x) * 2.0

    # Randomly set red ball starting position.
    red_ball.x = rng.uniform(-4.5, 4.5)
    red_ball.y = rng.uniform(-2, 4)

    return Level(
        name="funnel_onto_pad",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        target_object="green_ball",
        goal_object="purple_platform",
        success_condition=success_condition,
        metadata={
            "description": "Make sure the green ball goes through the funnel and hits the purple pad"
        },
    )


register_level("funnel_onto_pad")(build_level)
