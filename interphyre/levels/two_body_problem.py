import numpy as np
from interphyre.objects import Ball, PhyreObject
from interphyre.level import Level
from typing import cast
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    green_ball_radius = rng.uniform(0.2, 0.7)
    blue_ball_radius = rng.uniform(0.2, 0.8)
    red_ball_radius = rng.uniform(0.4, 1)

    # Sample green ball first, accounting for its radius
    green_ball_x = rng.uniform(-5 + green_ball_radius, 5 - green_ball_radius)
    green_ball_y = rng.uniform(-3, 4.5)

    # Sample blue ball ensuring it doesn't overlap with green ball
    # Require minimum separation of radii sum + 0.1
    min_separation = green_ball_radius + blue_ball_radius + 0.1

    # Sample blue ball y-coordinate
    blue_ball_y = rng.uniform(0.5, 4.5)

    # Calculate horizontal distance needed based on vertical separation
    dy = blue_ball_y - green_ball_y
    min_horizontal_separation = np.sqrt(max(0, min_separation**2 - dy**2))

    # Sample blue ball x ensuring horizontal separation.
    left_low = -5 + blue_ball_radius
    left_high = min(green_ball_x - min_horizontal_separation, 5 - blue_ball_radius)
    right_low = max(green_ball_x + min_horizontal_separation, -5 + blue_ball_radius)
    right_high = 5 - blue_ball_radius

    valid_left = left_low <= left_high
    valid_right = right_low <= right_high

    pick_left = rng.random() < 0.5
    if (pick_left and valid_left) or (not valid_right and valid_left):
        blue_ball_x = rng.uniform(left_low, left_high)
    elif valid_right:
        blue_ball_x = rng.uniform(right_low, right_high)
    else:
        # Fallback when separation is impossible; clamp within bounds.
        blue_ball_x = float(
            np.clip(green_ball_x, -5 + blue_ball_radius, 5 - blue_ball_radius)
        )

    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    blue_ball = Ball(
        x=blue_ball_x,
        y=blue_ball_y,
        radius=blue_ball_radius,
        color="blue",
        dynamic=True,
    )

    red_ball = Ball(
        x=-3,
        y=2.5,
        radius=red_ball_radius,
        color="red",
        dynamic=True,
    )

    objects = {
        "green_ball": green_ball,
        "blue_ball": blue_ball,
        "red_ball": red_ball,
    }

    return Level(
        name="two_body_problem",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball"},
    )
