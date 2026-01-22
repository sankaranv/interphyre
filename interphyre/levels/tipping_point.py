import numpy as np
from typing import cast
from interphyre.objects import Ball, Basket, Bar, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_bar", "purple_wall", success_time)


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    basket_x = rng.uniform(-4.5, 4.5)
    bar_length = rng.uniform(2, 5)

    basket = Basket(
        x=basket_x,
        y=-4.9,
        scale=0.45,
        wall_thickness=0.15,
        anchor="bottom_center",
        color="gray",
        dynamic=True,
        density=0.25,
        restitution=0.2,
    )

    bar_bottom = -4.9 + basket.floor_thickness + 0.02
    green_bar = Bar(
        x=basket_x,
        y=bar_bottom + bar_length / 2,
        length=bar_length,
        angle=90.0,
        thickness=0.2,
        color="green",
        dynamic=True,
        density=0.25,
        restitution=0.2,
    )

    # Wall must be reachable when bar tips over
    # Bar pivots from basket, so reach is approximately bar_length from basket_x
    dist_to_left_wall = basket_x - (-4.9)
    dist_to_right_wall = 4.9 - basket_x

    # Check which wall the bar can actually reach
    can_reach_left = bar_length >= dist_to_left_wall
    can_reach_right = bar_length >= dist_to_right_wall

    if can_reach_left and can_reach_right:
        # Can reach both - pick the closer one
        wall_x = -4.9 if dist_to_left_wall < dist_to_right_wall else 4.9
    elif can_reach_left:
        wall_x = -4.9
    elif can_reach_right:
        wall_x = 4.9
    else:
        # Bar can't reach either wall - skip this configuration
        # For now, pick the closer wall (level may be unsolvable)
        wall_x = -4.9 if basket_x < 0 else 4.9

    purple_wall = Bar(
        top=5.0,
        bottom=-5.0,
        x=wall_x,
        thickness=0.2,
        color="purple",
        dynamic=False,
    )

    red_ball_radius = rng.uniform(0.3, 0.6)
    red_ball = Ball(
        x=0,
        y=0,
        radius=red_ball_radius,
        color="red",
        dynamic=True,
    )

    objects = {
        "green_bar": green_bar,
        "red_ball": red_ball,
        "purple_wall": purple_wall,
        "basket": basket,
    }

    return Level(
        name="tipping_point",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={"description": "Make the green bar tip over and hit the wall"},
    )
