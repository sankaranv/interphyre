import numpy as np
from phyre2.objects import Ball, PhyreObject, Platform, Basket
from phyre2.level import Level
from typing import cast
from phyre2.levels import register_level


def success_condition(engine):
    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_jar", success_time)


def build_level(seed=None):
    rng = np.random.default_rng(seed)

    bar_height = rng.uniform(-1, 3.5)

    left_bar = Platform(
        x=-3,
        y=bar_height,
        length=4,
        angle=0,
        color="black",
        dynamic=False,
    )
    right_bar = Platform(
        x=3,
        y=bar_height,
        length=4,
        angle=0,
        color="black",
        dynamic=False,
    )

    bottom_ramp = Platform(
        x=0,
        y=-4,
        length=11,
        angle=11,
        color="black",
        dynamic=False,
    )

    blue_jar_y = rng.uniform(bar_height + 1, 4.5)
    blue_jar = Basket(
        x=rng.uniform(-0.5, 0.5),
        y=blue_jar_y,
        scale=0.8,
        color="blue",
        angle=180,
        dynamic=True,
    )

    green_ball_radius = 0.5
    green_ball = Ball(
        x=rng.choice([rng.uniform(-3, -1.5), rng.uniform(1.5, 3)]),
        y=bar_height + green_ball_radius,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    red_ball_radius = rng.uniform(0.4, min(1, (5 - bar_height) / 2))
    red_ball = Ball(
        x=-3,
        y=2.5,
        radius=red_ball_radius,
        color="red",
        dynamic=True,
    )

    objects = {
        "green_ball": green_ball,
        "blue_jar": blue_jar,
        "red_ball": red_ball,
        "left_bar": left_bar,
        "right_bar": right_bar,
        "bottom_ramp": bottom_ramp,
    }

    return Level(
        name="pinhole_jar",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball"},
    )


register_level("pinhole_jar")(build_level)
