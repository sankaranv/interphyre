import numpy as np
from typing import cast
from phyre2.objects import Ball, Platform, Basket, PhyreObject
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):

    return engine.is_in_basket_sensor("basket", "green_ball")


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    objects = {}

    # Add green ball at top
    green_ball_x = rng.uniform(-2.5, 2.5)
    green_ball_radius = rng.uniform(0.2, 0.3)
    objects["green_ball"] = Ball(
        x=green_ball_x,
        y=5 - green_ball_radius,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    staircase_angle = rng.uniform(-10, -5)
    staircase_top = rng.uniform(3, 4.5)
    stair_height = 1.1
    stair_length = (9.95 / 5) - 2 * green_ball_radius - 0.05
    # Add staircase platforms (for i=0,...,4)
    for i in range(5):
        objects[f"stair_{i+1}"] = Platform(
            x=-5
            + stair_length / 2
            + 0.5 * i * (5 - green_ball_radius - 0.05 - stair_length / 2),
            y=staircase_top - i * stair_height,
            length=stair_length,
            thickness=0.2,
            angle=staircase_angle,
            color="black",
            dynamic=False,
        )

    # Add red action ball
    red_ball_x = rng.uniform(-2.5, 2.5)
    red_ball_y = rng.uniform(1, 6.5)
    red_ball_radius = rng.uniform(0.4, 1)
    objects["red_ball"] = Ball(
        x=red_ball_x,
        y=red_ball_y,
        radius=red_ball_radius,
        color="red",
        dynamic=True,
    )

    basket_scale = rng.uniform(1.0, 2.0)
    basket_x = rng.uniform(-2.5, 2.5)
    basket_y = -5 + 0.1 * np.sqrt(basket_scale)
    objects["basket"] = Basket(
        x=basket_x,
        y=basket_y,
        scale=basket_scale,
        angle=0.0,
        color="purple",
        dynamic=True,
    )

    barrier_length = round(1.67 * basket_scale, 2) + 0.2
    barrier_thickness = round(0.05 + 0.1 * np.sqrt(basket_scale), 2)
    objects["left_barrier"] = Platform(
        x=basket_x - round(0.79 * basket_scale + barrier_thickness / 2, 2),
        y=-5 + (barrier_length) / 2,
        length=barrier_length,
        thickness=barrier_thickness,
        angle=90.0,
        color="black",
        dynamic=False,
    )
    objects["right_barrier"] = Platform(
        x=basket_x + round(0.79 * basket_scale + barrier_thickness / 2, 2),
        y=-5 + (barrier_length) / 2,
        length=barrier_length,
        thickness=barrier_thickness,
        angle=90.0,
        color="black",
        dynamic=False,
    )

    return Level(
        name="staircase",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Make sure the green ball falls into the purple basket",
        },
    )


register_level("staircase")(build_level)
