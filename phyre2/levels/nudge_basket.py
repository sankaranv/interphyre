import numpy as np
from typing import cast
from phyre2.objects import Ball, Platform, PhyreObject, Basket
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):
    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    basket_scale = rng.uniform(1, 1.5)
    ledge_y = rng.uniform(-2, -1)
    ledge_x = rng.choice([-1, 1]) * rng.uniform(1, 2)
    ledge_length = 3 * basket_scale
    ledge_angle = rng.uniform(0, 10)
    ledge_angle = -ledge_angle if ledge_x < 0 else ledge_angle
    basket_x = ledge_x + ledge_length / 2

    ledge = Platform(
        x=ledge_x,
        y=ledge_y,
        length=ledge_length,
        angle=ledge_angle,
        color="black",
        dynamic=False,
    )

    basket = Basket(
        x=0,
        y=-4.9,
        scale=basket_scale,
        angle=0,
        color="gray",
        dynamic=True,
    )

    blue_ball = Ball(
        x=0,
        y=-4.5,
        radius=0.4,
        color="blue",
        dynamic=True,
    )

    green_ball_radius = 0.2
    # green_ball_x = ledge_x + (
    #     np.sign(ledge_x) * ledge_length / 2 - green_ball_radius
    # ) * np.tan(np.radians(ledge_angle))
    # green_ball_y = ledge_y + (np.sign(ledge_x) * ledge_length / 2) / np.tan(
    #     np.radians(ledge_angle)
    # )
    green_ball_x = ledge_x + np.sign(ledge_x) * (
        ledge_length / 2 - 2 * green_ball_radius
    )
    green_ball_y = ledge_y + 2 * green_ball_radius + 0.5
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )
    red_ball = Ball(
        x=0.0,
        y=0.0,
        radius=rng.uniform(0.4, 0.8),
        color="red",
        dynamic=True,
    )

    ramp_angle = rng.uniform(30.0, 60.0)
    ramp_y = -4
    ramp_x = 3.75
    ramp_length = (5 - ramp_x) / np.cos(np.radians(ramp_angle)) * 4

    left_ramp = Platform(
        x=-ramp_x,
        y=ramp_y,
        length=ramp_length,
        angle=-ramp_angle,
        color="black",
        dynamic=False,
    )
    right_ramp = Platform(
        x=ramp_x,
        y=ramp_y,
        length=ramp_length,
        angle=ramp_angle,
        color="black",
        dynamic=False,
    )

    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "left_ramp": left_ramp,
        "right_ramp": right_ramp,
        "blue_ball": blue_ball,
        "ledge": ledge,
        "basket": basket,
    }

    return Level(
        name="nudge_basket",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Push the basket so thegreen ball falls in and hits the blue ball"
        },
    )


register_level("nudge_basket")(build_level)
