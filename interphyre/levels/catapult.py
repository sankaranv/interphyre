import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, PhyreObject, Basket
from interphyre.level import Level
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    black_ball_radius = 0.4
    black_ball_x = rng.uniform(-4, -1)
    black_ball = Ball(
        x=black_ball_x,
        y=5 - black_ball_radius,
        radius=black_ball_radius,
        color="black",
        dynamic=False,
    )

    black_platform_x = rng.uniform(-3, -1.5)
    black_platform_y = rng.uniform(-4, -2)
    black_platform_length = 3
    black_platform = Bar(
        left=black_platform_x - black_platform_length / 2,
        right=black_platform_x + black_platform_length / 2,
        y=black_platform_y,
        color="black",
        dynamic=False,
    )

    gray_ball_radius = 0.7
    gray_ball_x = black_platform.left + 3 * gray_ball_radius
    gray_ball_y = black_platform_y + gray_ball_radius
    gray_ball = Ball(
        x=gray_ball_x,
        y=gray_ball_y,
        radius=gray_ball_radius,
        color="gray",
        dynamic=True,
    )

    gray_platform_x = gray_ball_x
    gray_platform_y = gray_ball_y + gray_ball_radius + 0.1
    gray_platform_length = 4.25
    gray_platform = Bar(
        left=gray_platform_x - gray_platform_length / 2,
        right=gray_platform_x + gray_platform_length / 2,
        y=gray_platform_y,
        color="gray",
        dynamic=True,
    )

    green_ball_radius = 0.2
    green_ball_x = gray_platform.left + green_ball_radius
    green_ball_y = gray_platform_y + 0.1 + green_ball_radius
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    # ENHANCED: Use from_corner to eliminate trigonometry
    ledge_angle = rng.uniform(-10, 10)
    ledge_center_x = 3.5
    ledge_center_y = rng.uniform(-4, -2)
    ledge_length = 3 / np.cos(np.radians(ledge_angle))

    # Calculate corner position for from_corner
    ledge_corner_x = ledge_center_x - (ledge_length / 2) * np.cos(np.radians(ledge_angle))
    ledge_corner_y = ledge_center_y - (ledge_length / 2) * np.sin(np.radians(ledge_angle))

    ledge = Bar.from_corner(
        corner_x=ledge_corner_x,
        corner_y=ledge_corner_y,
        angle=ledge_angle,
        length=ledge_length,
        thickness=0.2,
        color="black",
        dynamic=False,
    )

    basket_x = ledge_center_x
    basket_y = ledge_center_y + 0.2 / np.cos(np.radians(ledge_angle))
    basket_scale = rng.uniform(0.75, 1.2)

    basket = Basket(
        x=basket_x,
        y=basket_y,
        scale=basket_scale,
        angle=ledge_angle,
        anchor="bottom_center",
        color="gray",
        dynamic=True,
    )

    blue_ball_radius = round(0.4 * basket_scale, 2)
    blue_ball_x = basket_x
    blue_ball_y = basket_y + blue_ball_radius + 0.2
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
        radius=rng.uniform(0.6, 1.2),
        color="red",
        dynamic=True,
    )

    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "blue_ball": blue_ball,
        "ledge": ledge,
        "basket": basket,
        "black_ball": black_ball,
        "black_platform": black_platform,
        "gray_ball": gray_ball,
        "gray_platform": gray_platform,
    }

    return Level(
        name="catapult",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Push the basket so the green ball falls in and hits the blue ball"
        },
    )
