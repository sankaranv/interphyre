import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, Basket, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level


def success_condition(engine):

    return engine.is_in_basket("basket", "green_ball")


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    objects = {}

    green_ball_radius = rng.uniform(0.2, 0.3)
    staircase_angle = rng.uniform(-10, -5)
    staircase_top = rng.uniform(3, 4.5)
    stair_height = 1.1
    stair_length = (9.95 / 5) - 2 * green_ball_radius - 0.05

    # Create the staircase first
    for i in range(5):
        center_x = (
            -5
            + stair_length / 2
            + 0.5 * i * (5 - green_ball_radius - 0.05 - stair_length / 2)
        )
        center_y = staircase_top - i * stair_height

        objects[f"stair_{i+1}"] = Bar.from_point_and_angle(
            x=center_x,
            y=center_y,
            angle=staircase_angle,
            length=stair_length,
            thickness=0.2,
            color="black",
            dynamic=False,
        )

    # Select a random slat from 0 to 3 and place ball at its right edge
    selected_slat = rng.integers(0, 4)  # 0 to 3 inclusive
    green_ball_x = objects[f"stair_{selected_slat+1}"].right

    objects["green_ball"] = Ball(
        x=green_ball_x,
        y=5 - green_ball_radius,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

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
    basket_y = -5 + 0.1 * np.sqrt(basket_scale) + 0.1
    objects["basket"] = Basket(
        x=basket_x,
        y=basket_y,
        scale=basket_scale,
        angle=0.0,
        anchor="bottom_center",
        color="purple",
        dynamic=True,
    )

    basket_obj = objects["basket"]
    barrier_length = round(basket_obj.height, 2) + 0.2
    barrier_thickness = round(basket_obj.wall_thickness, 2)
    barrier_offset = round(basket_obj.top_width / 2 + barrier_thickness * 2, 2)

    objects["left_barrier"] = Bar.from_point_and_angle(
        x=basket_x - barrier_offset,
        y=-5 + (barrier_length) / 2,
        angle=90.0,
        length=barrier_length,
        thickness=barrier_thickness,
        color="black",
        dynamic=False,
    )

    objects["right_barrier"] = Bar.from_point_and_angle(
        x=basket_x + barrier_offset,
        y=-5 + (barrier_length) / 2,
        angle=90.0,
        length=barrier_length,
        thickness=barrier_thickness,
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
