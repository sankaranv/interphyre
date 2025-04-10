import numpy as np
from typing import cast
from phyre2.objects import Ball, Platform, Basket, PhyreObject
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):
    # Level designers can simply refer to object names:
    return engine.has_contact("green_ball", "basket")


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    # Determine positions and sizes using randomness
    green_ball_x = rng.uniform(-2.5, 2.5)
    green_ball_r = rng.uniform(0.2, 0.3)
    red_ball_x = rng.uniform(-2.5, 2.5)
    red_ball_y = rng.uniform(1, 6.5)
    basket_scale = rng.uniform(1.0, 2.0)
    basket_y = 0.1 + basket_scale * 0.083
    barrier_length = basket_scale * 1.2

    objects = {}

    # Add staircase platforms (for i=0,...,4)
    for i in range(5):
        objects[f"stair_{i+1}_platform"] = Platform(
            x=-2.25 + i * 1.0,
            y=6.0 - i * 1.2,
            length=0.5,
            thickness=0.1,
            angle=-5,
            color="black",
            dynamic=False,
        )

    # Add green ball at top
    objects["green_ball"] = Ball(
        x=green_ball_x,
        y=8.8,
        radius=green_ball_r,
        color="green",
        dynamic=True,
    )

    # Add red action ball
    objects["red_ball"] = Ball(
        x=red_ball_x,
        y=red_ball_y,
        radius=0.3,
        color="red",
        dynamic=True,
    )

    # Add dynamic basket as goal target
    objects["basket"] = Basket(
        x=0.0,
        y=basket_y,
        scale=basket_scale,
        angle=0.0,
        color="purple",
        dynamic=True,
    )

    # Add barrier platforms to guide the ball into the basket
    objects["left_barrier_platform"] = Platform(
        x=-basket_scale * 0.6,
        y=0.2,
        length=barrier_length,
        thickness=0.1,
        angle=90.0,
        color="black",
        dynamic=False,
    )
    objects["right_barrier_platform"] = Platform(
        x=basket_scale * 0.6,
        y=0.2,
        length=barrier_length,
        thickness=0.1,
        angle=90.0,
        color="black",
        dynamic=False,
    )

    # Add the ground platform
    objects["ground"] = Platform(
        x=0.0,
        y=0.0,
        length=10.0,
        thickness=0.2,
        angle=0.0,
        color="black",
        dynamic=False,
    )

    return Level(
        name="staircase",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        target_object="green_ball",
        goal_object="basket",
        success_condition=success_condition,
        metadata={
            "description": "Make sure the green ball goes through the funnel and hits the purple pad",
        },
    )


register_level("staircase")(build_level)
