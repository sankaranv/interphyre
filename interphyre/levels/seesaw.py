import numpy as np
from interphyre.objects import Ball, Bar, PhyreObject
from interphyre.level import Level
from typing import cast
from interphyre.levels import register_level
from interphyre.render import MIN_X, MAX_X


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "blue_platform", success_time
    )


@register_level
def build_level(seed=None):
    rng = np.random.default_rng(seed)

    valid_level_found = False
    black_ball_radius = 0.4

    while not valid_level_found:
        floor_y = rng.uniform(-4.7, 2.5)
        blue_platform_length = rng.uniform(3, 5)
        platform_thickness = 0.2

        black_ball_x = rng.uniform(
            MIN_X + blue_platform_length / 2 + black_ball_radius,
            MAX_X - blue_platform_length / 2 - black_ball_radius,
        )

        blue_platform_y = (floor_y + 2 * black_ball_radius + 0.1) + (
            platform_thickness / 2
        )
        blue_platform_x = black_ball_x

        # Calculate barrier positions with proper gap to prevent trivial solutions
        green_ball_radius = 0.4
        barrier_length = 2
        ball_diameter = 2 * green_ball_radius

        max_offset = min(
            MAX_X - blue_platform_x - barrier_length / 2,
            blue_platform_x - MIN_X - barrier_length / 2,
        )
        min_offset = blue_platform_length / 2 + ball_diameter + 0.1

        if min_offset >= max_offset:
            continue

        barrier_offset_x = rng.uniform(min_offset, max_offset)
        left_barrier_x = blue_platform_x - barrier_offset_x
        right_barrier_x = blue_platform_x + barrier_offset_x

        # Push barriers out of bounds if too close to edge
        left_barrier_x = MIN_X - 0.1 if left_barrier_x < MIN_X + 0.1 else left_barrier_x
        right_barrier_x = (
            MAX_X + 0.1 if right_barrier_x > MAX_X - 0.1 else right_barrier_x
        )

        barrier_thickness = 0.2
        green_ball_y = MAX_X - green_ball_radius - 0.1
        min_clearance_from_ball = 1.0
        max_barrier_top = green_ball_y - min_clearance_from_ball

        min_barrier_y = floor_y + barrier_length / 2
        max_barrier_y = max_barrier_top - barrier_length / 2
        max_barrier_y_constrained = min(MAX_X - barrier_length / 2, max_barrier_y)

        if min_barrier_y >= max_barrier_y_constrained:
            continue

        barrier_y = rng.uniform(min_barrier_y, max_barrier_y_constrained)

        # Position green ball on platform ends to prevent trivial solutions
        blue_platform = Bar.from_point_and_angle(
            x=blue_platform_x,
            y=blue_platform_y,
            length=blue_platform_length,
            angle=0.0,
            color="blue",
            dynamic=True,
        )

        if rng.random() < 0.5:
            green_ball_x = blue_platform.left + green_ball_radius + 0.1
        else:
            green_ball_x = blue_platform.right - green_ball_radius - 0.1

        valid_level_found = True

    green_ball_y = MAX_X - green_ball_radius - 0.1

    floor = Bar.from_point_and_angle(
        x=0.0,
        y=floor_y,
        length=10.0,
        angle=0.0,
        color="black",
        dynamic=False,
    )

    black_ball = Ball(
        x=black_ball_x,
        y=floor_y + black_ball_radius + 0.1,
        radius=black_ball_radius,
        color="black",
        dynamic=False,
    )

    left_barrier = Bar.support_leg(
        top_x=left_barrier_x,
        top_y=barrier_y + barrier_length / 2,
        bottom_x=left_barrier_x,
        bottom_y=barrier_y - barrier_length / 2,
        thickness=barrier_thickness,
        color="black",
        dynamic=False,
    )

    right_barrier = Bar.support_leg(
        top_x=right_barrier_x,
        top_y=barrier_y + barrier_length / 2,
        bottom_x=right_barrier_x,
        bottom_y=barrier_y - barrier_length / 2,
        thickness=barrier_thickness,
        color="black",
        dynamic=False,
    )

    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    red_ball_radius = rng.uniform(0.2, 0.8)
    red_ball_y = max(MIN_X + 0.1, floor_y + red_ball_radius + 0.1)

    red_ball_x_candidates = []
    for x in np.linspace(
        MIN_X + 0.5 + red_ball_radius, MAX_X - 0.5 - red_ball_radius, 20
    ):
        if (
            abs(x - black_ball_x) > (black_ball_radius + red_ball_radius + 0.1)
            and abs(x - green_ball_x) > (green_ball_radius + red_ball_radius + 0.1)
            and abs(x - left_barrier.left)
            > (barrier_thickness / 2 + red_ball_radius + 0.1)
            and abs(x - right_barrier.left)
            > (barrier_thickness / 2 + red_ball_radius + 0.1)
        ):
            red_ball_x_candidates.append(x)

    if red_ball_x_candidates:
        red_ball_x = rng.choice(red_ball_x_candidates)
    else:
        red_ball_x = rng.uniform(
            MIN_X + 0.5 + red_ball_radius, MAX_X - 0.5 - red_ball_radius
        )

    red_ball = Ball(
        x=red_ball_x,
        y=red_ball_y,
        radius=red_ball_radius,
        color="red",
        dynamic=True,
    )

    objects = {
        "floor": floor,
        "green_ball": green_ball,
        "red_ball": red_ball,
        "black_ball": black_ball,
        "blue_platform": blue_platform,
        "left_barrier": left_barrier,
        "right_barrier": right_barrier,
    }

    return Level(
        name="seesaw",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={"description": "Make sure the green ball is touching the blue bar"},
    )
