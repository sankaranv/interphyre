import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "bottom_wall", success_time)


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    # Level parameters
    hole_left_x = rng.uniform(-2.0, 1.0)
    hole_width = 1.0
    hole_right_x = hole_left_x + hole_width

    platform_y = rng.uniform(-3.5, 1.0)
    block_left_side = rng.choice([True, False])

    # Ball sizes
    green_ball_radius = 0.5
    blocking_ball_radius = 0.55
    green_ball_y = 3.5

    left_platform = Bar(
        left=MIN_X,
        right=hole_left_x,
        y=platform_y,
        thickness=0.2,
        color="black",
        dynamic=False,
    )

    right_platform = Bar(
        left=hole_right_x,
        right=MAX_X,
        y=platform_y,
        thickness=0.2,
        color="black",
        dynamic=False,
    )

    # Green ball starts at center-top
    green_ball = Ball(
        x=0.0,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    # Blocking ball positioned above platform by ball_distance
    blocker_distance_from_platform = rng.uniform(1.0, 3.0)
    blocker_bottom = platform_y + blocker_distance_from_platform
    blocker_y = blocker_bottom + blocking_ball_radius

    # Position blocker at hole edge with 0.25 offset, accounting for radius
    if block_left_side:
        blocker_x = hole_left_x + 0.25 + blocking_ball_radius
    else:
        blocker_x = hole_right_x - 0.25 - blocking_ball_radius

    blocking_ball = Ball(
        x=blocker_x,
        y=blocker_y,
        radius=blocking_ball_radius,
        color="gray",
        dynamic=True,
    )

    # Ensure green ball isn't directly over the hole
    if (
        green_ball.x - green_ball_radius >= hole_left_x
        and green_ball.x + green_ball_radius <= hole_right_x
    ):
        green_ball.x = hole_left_x - green_ball_radius - 0.1

    # Bottom wall
    bottom_wall = Bar(
        left=MIN_X,
        right=MAX_X,
        y=MIN_Y,
        thickness=0.2,
        color="black",
        dynamic=False,
    )

    # User-placeable red ball
    red_ball = Ball(
        x=0.0,
        y=0.0,
        radius=0.5,
        color="red",
        dynamic=True,
    )

    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "blocking_ball": blocking_ball,
        "bottom_wall": bottom_wall,
        "left_platform": left_platform,
        "right_platform": right_platform,
    }

    return Level(
        name="mind_the_gap",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={"description": "Push the green ball through the gap to reach the ground."},
    )
