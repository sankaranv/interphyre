import numpy as np
from typing import cast
from phyre2.objects import Ball, Basket, Bar, PhyreObject
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):
    # Success is defined as the green ball contacting the angled platform (i.e. hitting the ground)
    # while not contacting the basket.
    return engine.has_contact(
        "green_ball", "angled_platform"
    ) and not engine.has_contact("green_ball", "basket")


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    # Create objects with fixed base values.
    green_ball = Ball(
        x=0.0,
        y=4.9,
        radius=1.0,
        color="green",
        dynamic=True,
    )
    red_ball = Ball(
        x=0.0,
        y=0.0,
        radius=0.4,
        color="red",
        dynamic=True,
    )
    left_platform = Bar(
        x=-3.0,
        y=0.0,
        length=2.0,
        angle=0.0,
        color="black",
        dynamic=False,
    )
    right_platform = Bar(
        x=3.0,
        y=0.0,
        length=2.0,
        angle=0.0,
        color="black",
        dynamic=False,
    )
    angled_platform = Bar(
        x=0.0,
        y=-3.9,
        length=5.5,
        angle=10.0,
        color="black",
        dynamic=False,
    )
    basket = Basket(
        x=0.0,
        y=-4.9,
        scale=0.7,
        angle=180.0,
        color="blue",
        dynamic=True,
    )

    # Randomize left and right platform y-position.
    left_platform.y = rng.uniform(-0.5, 1)
    right_platform.y = left_platform.y

    # Randomize basket position.
    basket.x = rng.uniform(-0.5, 0.5)
    basket.y = left_platform.y + rng.uniform(1, 2)

    # Randomize green ball radius and set its position relative to the left platform.
    green_ball.radius = rng.uniform(0.2, 0.5)
    green_ball.x = rng.choice([rng.uniform(-4.5, -1.5), rng.uniform(1.5, 4.5)])
    green_ball.y = left_platform.y + green_ball.radius

    # Randomize red ball starting position.
    red_ball.x = rng.uniform(-4.5, 4.5)
    red_ball.y = rng.uniform(-2, 4)

    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "left_platform": left_platform,
        "right_platform": right_platform,
        "angled_platform": angled_platform,
        "basket": basket,
    }

    return Level(
        name="hit_basket",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        target_object="green_ball",
        goal_object="basket",  # The basket is set as the goal, but the success condition will require avoiding contact.
        success_condition=success_condition,
        metadata={
            "description": "Make sure the green ball hits the ground and stays out of the basket"
        },
    )


register_level("hit_basket")(build_level)
