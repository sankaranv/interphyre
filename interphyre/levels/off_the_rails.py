import numpy as np
from typing import cast
from interphyre.objects import Ball, Basket, Bar, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level


def success_condition(engine):

    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "purple_wall", success_time)


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    corner_point_x = rng.uniform(-2.25, 2.25)
    corner_point_y = -5

    purple_wall_angle = rng.uniform(10, 50)
    purple_wall_length = np.abs(5 - corner_point_x) / np.cos(
        np.radians(purple_wall_angle)
    )
    purple_wall_x = (
        corner_point_x + np.cos(np.radians(purple_wall_angle)) * purple_wall_length / 2
    )
    purple_wall_y = (
        corner_point_y + np.sin(np.radians(purple_wall_angle)) * purple_wall_length / 2
    )
    purple_wall = Bar(
        x=purple_wall_x,
        y=purple_wall_y,
        length=purple_wall_length,
        angle=purple_wall_angle,
        color="purple",
        dynamic=False,
    )

    black_wall_angle = rng.uniform(25, 55)
    black_wall_horiz_dist = np.abs(corner_point_x - (-5))
    black_wall_length = black_wall_horiz_dist / np.cos(np.radians(black_wall_angle))
    black_wall_x = (corner_point_x + (-5)) / 2
    black_wall_y = (
        corner_point_y + np.sin(np.radians(black_wall_angle)) * black_wall_length / 2
    )
    black_wall = Bar(
        x=black_wall_x,
        y=black_wall_y,
        length=black_wall_length,
        angle=180 - black_wall_angle,
        color="black",
        dynamic=False,
    )

    left_edge_y = -5 + np.abs(-5 - corner_point_x) * np.tan(
        np.radians(black_wall_angle)
    )
    basket_y = min(max(left_edge_y + 0.6, 2), 4)

    basket_x = min((5 - basket_y) / np.tan(np.radians(black_wall_angle)) + 0.5, -4.25)
    basket = Basket(
        x=basket_x,
        y=basket_y,
        scale=1.0,
        angle=-black_wall_angle,
        color="gray",
        dynamic=True,
    )

    green_ball_radius = 0.4
    green_ball_x_offset = 2 * green_ball_radius * np.cos(np.radians(black_wall_angle))
    green_ball_y_offset = 2 * green_ball_radius * np.sin(np.radians(black_wall_angle))
    green_ball = Ball(
        x=basket_x + green_ball_x_offset,
        y=basket_y + green_ball_y_offset,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )
    red_ball = Ball(
        x=0.0,
        y=0.0,
        radius=0.5,
        color="red",
        dynamic=True,
    )

    # Assemble objects dictionary.
    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "purple_wall": purple_wall,
        "black_wall": black_wall,
        "basket": basket,
    }

    return Level(
        name="off_the_rails",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Get the green ball out of the basket and onto the purple wall"
        },
    )
