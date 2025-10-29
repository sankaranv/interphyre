import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, Basket, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level


def success_condition(engine):

    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_ground", success_time
    )


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    purple_ground = Bar.from_point_and_angle(
        x=0.0,
        y=-4.9,
        length=10.0,
        thickness=0.2,
        angle=0.0,
        color="purple",
        dynamic=False,
    )

    # Gap width equals ball diameter plus a small margin so green ball can fall through
    green_ball_radius = 0.4
    pinhole_width = 2 * green_ball_radius + 0.1
    pinhole_x = rng.uniform(-2, 2)  # Random gap position
    platform_y = rng.uniform(-2, 2)

    left_gap_edge = pinhole_x - pinhole_width / 2
    left_platform_length = left_gap_edge - (-5)
    left_platform_x = -5 + left_platform_length / 2

    right_gap_edge = pinhole_x + pinhole_width / 2
    right_platform_length = 5 - right_gap_edge
    right_platform_x = 5 - right_platform_length / 2

    left_platform = Bar.from_point_and_angle(
        x=left_platform_x,
        y=platform_y,
        length=left_platform_length,
        thickness=0.2,
        angle=0.0,
        color="black",
        dynamic=False,
    )

    right_platform = Bar.from_point_and_angle(
        x=right_platform_x,
        y=platform_y,
        length=right_platform_length,
        thickness=0.2,
        angle=0.0,
        color="black",
        dynamic=False,
    )

    # Gray ball covers part of gap but cannot fit through (radius > gap width/2)
    gray_ball_radius = 0.5
    gap_left = pinhole_x - pinhole_width / 2
    gap_right = pinhole_x + pinhole_width / 2

    # Position gray ball to cover either left or right side of gap
    overlap_amount = rng.uniform(0.1, 0.3)
    if rng.random() < 0.5:
        gray_ball_x = gap_left + overlap_amount
    else:
        gray_ball_x = gap_right - overlap_amount

    # Position gray ball above platform with space for red ball underneath
    required_space = 0.3
    min_gray_y = platform_y + gray_ball_radius + required_space
    gray_ball_y = rng.uniform(min_gray_y, min_gray_y + 1.5)

    # Green ball positioned based on which side of gap gray ball covers
    min_separation = green_ball_radius + gray_ball_radius
    gap_center = pinhole_x

    if gray_ball_x < gap_center:
        # Gray ball covers left side, green ball goes left
        green_ball_x = gray_ball_x - rng.uniform(0.2, gray_ball_radius)
    else:
        # Gray ball covers right side, green ball goes right
        green_ball_x = gray_ball_x + rng.uniform(0.2, gray_ball_radius)

    # Ensure minimum separation is maintained
    current_distance = abs(green_ball_x - gray_ball_x)
    if current_distance < min_separation:
        direction = 1 if green_ball_x > gray_ball_x else -1
        green_ball_x = gray_ball_x + direction * min_separation

    green_ball_x = np.clip(green_ball_x, -4, 4)

    # Position green ball above gray ball
    min_green_y = gray_ball_y + min_separation + 0.1
    max_green_y = 5 - green_ball_radius
    if min_green_y <= max_green_y:
        green_ball_y = rng.uniform(min_green_y, max_green_y)
    else:
        green_ball_y = 4.5

    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )
    gray_ball = Ball(
        x=gray_ball_x,
        y=gray_ball_y,
        radius=gray_ball_radius,
        color="gray",
        dynamic=True,
    )

    red_ball_x = rng.uniform(-4.5, 4.5)
    red_ball_y = rng.uniform(-2, 4)
    red_ball_radius = rng.uniform(0.3, 0.7)
    red_ball = Ball(
        x=red_ball_x,
        y=red_ball_y,
        radius=red_ball_radius,
        color="red",
        dynamic=True,
    )

    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "gray_ball": gray_ball,
        "purple_ground": purple_ground,
        "left_platform": left_platform,
        "right_platform": right_platform,
    }

    return Level(
        name="pinhole",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball hit the ground"},
    )
