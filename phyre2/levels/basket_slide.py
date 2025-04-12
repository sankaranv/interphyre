import numpy as np
from typing import cast
from phyre2.objects import Ball, Basket, Platform, PhyreObject
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):
    # Define success: the green ball contacts the purple platform.
    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "purple_wall", success_time)


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    # Create initial objects with fixed parameters.
    green_ball = Ball(
        x=0.0,
        y=-4.9,
        radius=0.4,
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
    # Initial purple_platform and black_platform (to be replaced later)
    purple_platform = Platform(
        x=0.0,
        y=0.0,
        length=3.0,
        angle=90.0,
        color="purple",
        dynamic=False,
    )
    black_platform = Platform(
        x=-4.0,
        y=-4.5,
        length=4.0,
        angle=75.0,
        color="black",
        dynamic=False,
    )
    basket = Basket(
        x=0.0,
        y=-4.9,
        scale=1.0,
        angle=0.0,
        color="gray",
        dynamic=True,
    )

    # Set level properties
    # Target: green_ball, Goal: purple_platform, Action objects: red_ball
    #
    # Create two platforms for the wall: right_platform and left_platform.
    center_x = rng.uniform(-1, 1)
    right_platform = Platform(
        x=0.0,
        y=0.0,
        length=7.0,
        angle=90.0,
        color="purple",  # initial placeholder
        dynamic=False,
    )
    left_platform = Platform(
        x=0.0,
        y=0.0,
        length=7.0,
        angle=90.0,
        color="black",  # initial placeholder
        dynamic=False,
    )

    # Set right platform attributes (simulate a wall touching the ground).
    right_platform.angle = rng.integers(10, 51)
    right_platform.x = (
        center_x
        + np.cos(right_platform.angle * np.pi / 180) * right_platform.length / 2
    )
    right_platform.y = (
        -5 + np.sin(right_platform.angle * np.pi / 180) * right_platform.length / 2
    )

    # Set left platform attributes.
    left_platform.angle = rng.integers(-60, -29)
    left_platform.x = (
        center_x - np.cos(left_platform.angle * np.pi / 180) * left_platform.length / 2
    )
    left_platform.y = (
        -5 - np.sin(left_platform.angle * np.pi / 180) * left_platform.length / 2
    )

    # Choose which platform becomes the purple platform (target wall) and which becomes black.
    if rng.uniform() < 0.5:
        left_platform.color = "purple"
        right_platform.color = "black"
        purple_platform = left_platform  # target: purple_platform
        black_platform = right_platform  # used later for basket alignment
    else:
        left_platform.color = "black"
        right_platform.color = "purple"
        purple_platform = right_platform
        black_platform = left_platform

    # Set basket position based on the black platform.
    basket.angle = black_platform.angle
    if black_platform.angle < 0:
        basket.x = black_platform.x - black_platform.length / 2
    else:
        basket.x = black_platform.x + black_platform.length / 2
    basket.y = black_platform.y + black_platform.length / 2
    basket.x = np.clip(basket.x, -4.5, 4.5)

    # Place the green ball inside the basket.
    if purple_platform.x < 0:
        green_ball.x = basket.x - 0.5
    else:
        green_ball.x = basket.x + 0.5
    green_ball.y = basket.y + 0.5

    # Randomly set red ball starting position (for passive mode).
    red_ball.x = rng.uniform(-4.5, 4.5)
    red_ball.y = rng.uniform(-2, 4)

    # Assemble objects dictionary.
    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "purple_platform": purple_platform,
        "black_platform": black_platform,
        "basket": basket,
    }

    return Level(
        name="basket_slide",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Get the green ball out of the basket and onto the purple wall"
        },
    )


register_level("escape_from_basket")(build_level)
