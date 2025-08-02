import numpy as np
from typing import cast
from interphyre.objects import Ball, Basket, Bar, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.render import MIN_X, MAX_X, MIN_Y

# TODO - increease friction so the jar doesn't slide around with small balls
# TODO - alternatively, prevent small balls with large baskets


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_ground", success_time
    )


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    bar_thickness = 0.2
    purple_ground = Bar(
        left=MIN_X,
        right=MAX_X,
        y=MIN_Y + bar_thickness / 2,
        color="purple",
        dynamic=False,
    )

    # Set basket starting position based on green_ball.
    basket_scale = rng.uniform(0.5, 2)
    basket_x = rng.uniform(-4.5 + basket_scale, 4.5 - basket_scale)
    basket_y = purple_ground.y + basket_scale + rng.uniform(0, 1)

    # Randomly set green ball attributes.
    green_ball_x = basket_x
    green_ball_y = rng.uniform(1, 4.5)
    green_ball_radius = rng.uniform(
        min(0.3, basket_scale * 0.5), max(0.3, basket_scale * 0.5)
    )

    # Randomly set red ball starting position.
    red_ball_x = rng.uniform(-4.5, 4.5)
    red_ball_y = rng.uniform(-2, 4)

    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )
    red_ball = Ball(
        x=red_ball_x,
        y=red_ball_y,
        radius=0.4,
        color="red",
        dynamic=True,
    )

    basket = Basket(
        x=basket_x,
        y=basket_y,
        scale=basket_scale,
        color="gray",
        dynamic=True,
    )

    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "purple_ground": purple_ground,
        "basket": basket,
    }

    return Level(
        name="basket_case",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Make sure the green ball hits the purple ground and is not trapped in the basket"
        },
    )
