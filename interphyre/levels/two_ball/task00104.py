import numpy as np
from typing import cast
from interphyre.objects import Ball, Basket, InterphyreObject
from interphyre.level import Level
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    ball_size = 0.1
    x_options = np.linspace(0.1, 0.9, 8)
    y_options = np.linspace(0.5, 0.8, 8)

    while True:
        ball1_x = rng.choice(x_options)
        ball2_x = rng.choice(x_options)
        if ball2_x > ball1_x + 0.2:
            break
    ball1_y = rng.choice(y_options)
    ball2_y = rng.choice(y_options)

    ball_radius = ball_size * (10.0) / 2
    green_ball_x = (ball1_x - 0.5) * (10.0)
    blue_ball_x = (ball2_x - 0.5) * (10.0)
    green_ball_y = (-5.0) + ball1_y * (10.0) + ball_radius
    blue_ball_y = (-5.0) + ball2_y * (10.0) + ball_radius

    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )
    blue_ball = Ball(
        x=blue_ball_x,
        y=blue_ball_y,
        radius=ball_radius,
        color="blue",
        dynamic=True,
    )

    basket_scale = 0.15 * (10.0) / 2
    green_basket = Basket(
        x=green_ball_x,
        y=(-5.0) + 0.1,
        scale=basket_scale,
        anchor="bottom_center",
        color="gray",
        dynamic=True,
    )
    blue_basket = Basket(
        x=blue_ball_x,
        y=(-5.0) + 0.1,
        scale=basket_scale,
        anchor="bottom_center",
        color="gray",
        dynamic=True,
    )

    red_ball_1 = Ball(
        x=-3.0,
        y=4.0,
        radius=0.5,
        color="red",
        dynamic=True,
    )
    red_ball_2 = Ball(
        x=3.0,
        y=4.0,
        radius=0.5,
        color="red",
        dynamic=True,
    )

    objects = {
        "green_ball": green_ball,
        "blue_ball": blue_ball,
        "green_basket": green_basket,
        "blue_basket": blue_basket,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00104",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
