import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, PhyreObject, Basket
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.render import MAX_X, MAX_Y


def success_condition(engine):
    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    black_platform_x = rng.uniform(1, 3)
    black_platform_y = rng.uniform(0, 3)
    black_platform_length = 2 * (MAX_X - black_platform_x)
    black_platform = Bar(
        x=black_platform_x,
        y=black_platform_y,
        length=black_platform_length,
        angle=0,
        color="black",
        dynamic=False,
    )

    ramp_angle = rng.uniform(10, 70)
    distance_to_right = (MAX_X - black_platform_x) / np.cos(np.radians(ramp_angle))
    distance_to_top = (MAX_Y - black_platform_y) / np.sin(np.radians(ramp_angle))
    ramp_length = min(distance_to_right, distance_to_top)
    ramp_x = black_platform_x + (ramp_length / 2) * np.cos(np.radians(ramp_angle))
    ramp_y = black_platform_y + (ramp_length / 2) * np.sin(np.radians(ramp_angle))
    ramp = Bar(
        x=ramp_x,
        y=ramp_y,
        length=ramp_length,
        angle=ramp_angle,
        color="black",
        dynamic=False,
    )

    top_basket_scale = 0.6
    top_basket_x = (
        black_platform_x - black_platform_length / 2 + top_basket_scale + 0.01
    )
    top_basket_y = black_platform_y + top_basket_scale + 0.1
    top_basket = Basket(
        x=top_basket_x,
        y=top_basket_y,
        scale=top_basket_scale,
        angle=180,
        color="gray",
        dynamic=True,
    )

    green_ball_radius = 0.25
    green_ball_x = top_basket_x - green_ball_radius - 0.1
    green_ball_y = top_basket_y - 2 * green_ball_radius
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    bottom_basket_scale = rng.uniform(0.7, 1.0)
    bottom_basket_x = black_platform_x - black_platform_length / 2 - bottom_basket_scale
    bottom_basket_y = -4.6
    bottom_basket = Basket(
        x=bottom_basket_x,
        y=bottom_basket_y,
        scale=bottom_basket_scale,
        angle=0,
        color="gray",
        dynamic=True,
    )

    blue_ball_radius = round(0.45 * bottom_basket_scale, 2)
    blue_ball_x = bottom_basket_x
    blue_ball_y = bottom_basket_y + blue_ball_radius + 0.2
    blue_ball = Ball(
        x=blue_ball_x,
        y=blue_ball_y,
        radius=blue_ball_radius,
        color="blue",
        dynamic=True,
    )

    red_ball = Ball(
        x=0.0,
        y=0.0,
        radius=rng.uniform(0.5, 0.8),
        color="red",
        dynamic=True,
    )

    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "blue_ball": blue_ball,
        "ramp": ramp,
        "top_basket": top_basket,
        "bottom_basket": bottom_basket,
        "black_platform": black_platform,
    }

    return Level(
        name="pass_the_parcel",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Push the basket so the green ball falls in and hits the blue ball"
        },
    )
