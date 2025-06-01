import numpy as np
from interphyre.objects import Ball, Bar, PhyreObject
from interphyre.level import Level
from typing import cast
from interphyre.levels import register_level


# TODO - some levels are unsolvable because the barriers are too high for the green ball to make it in
def success_condition(engine):
    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "blue_platform", success_time
    )


@register_level
def build_level(seed=None):
    rng = np.random.default_rng(seed)

    valid_level_found = False
    black_ball_radius = 0.4

    while not valid_level_found:
        # Floor placement (keeping within bounds)
        floor_y = rng.uniform(-4.7, 2.5)

        # Blue platform placement
        blue_platform_length = rng.uniform(
            3, min(5.5, 10 - 2 * black_ball_radius)
        )  # Ensure it fits
        platform_thickness = 0.2  # Default thickness

        # Black ball placement
        black_ball_x = rng.uniform(
            -5 + blue_platform_length / 2 + black_ball_radius,
            5 - blue_platform_length / 2 - black_ball_radius,
        )

        # Position blue platform centered directly above the black ball
        blue_platform_y = (floor_y + 2 * black_ball_radius + 0.1) + (
            platform_thickness / 2
        )
        blue_platform_x = black_ball_x

        # Calculate platform edges
        platform_left = blue_platform_x - blue_platform_length / 2
        platform_right = blue_platform_x + blue_platform_length / 2

        # Calculate barrier positions that respect minimum clearance from blue platform
        min_clearance = 0.2
        barrier_offset_x = rng.uniform(
            min(blue_platform_length / 2 + min_clearance, 5 - blue_platform_x),
            max(blue_platform_length / 2 + min_clearance, blue_platform_x - 5),
        )

        # Ensure these positions are within bounds
        left_barrier_x = blue_platform_x - barrier_offset_x
        right_barrier_x = blue_platform_x + barrier_offset_x

        # Push the barrier out of bounds if they are too close to the edge, effectively leaving one barrier in the scene
        left_barrier_x = -5.1 if left_barrier_x < -4.9 else left_barrier_x
        right_barrier_x = 5.1 if right_barrier_x > 4.9 else right_barrier_x

        # Ensure barrier height and length are valid
        barrier_length = rng.uniform(1, 4.5 - floor_y)
        barrier_y = rng.uniform(floor_y + barrier_length / 2, 5 - barrier_length / 2)

        # Green ball placement - accounting for clearance from barriers
        green_ball_radius = 0.4
        barrier_thickness = 0.2

        # Calculate zones where green ball can be placed, accounting for barriers and blue platform
        # Zone to the left of left barrier
        left_zone_max = (
            left_barrier_x - (barrier_thickness / 2) - green_ball_radius - min_clearance
        )
        left_zone_min = -5 + green_ball_radius + 0.1
        valid_left_zone = left_zone_min < left_zone_max

        # Zone between left barrier and blue platform
        mid_left_zone_max = platform_left - green_ball_radius - min_clearance
        mid_left_zone_min = (
            left_barrier_x + (barrier_thickness / 2) + green_ball_radius + min_clearance
        )
        valid_mid_left_zone = mid_left_zone_min < mid_left_zone_max

        # Zone between blue platform and right barrier
        mid_right_zone_max = (
            right_barrier_x
            - (barrier_thickness / 2)
            - green_ball_radius
            - min_clearance
        )
        mid_right_zone_min = platform_right + green_ball_radius + min_clearance
        valid_mid_right_zone = mid_right_zone_min < mid_right_zone_max

        # Zone to the right of right barrier
        right_zone_max = 5 - green_ball_radius - 0.1
        right_zone_min = (
            right_barrier_x
            + (barrier_thickness / 2)
            + green_ball_radius
            + min_clearance
        )
        valid_right_zone = right_zone_min < right_zone_max

        # Collect all valid zones
        valid_zones = []
        if valid_left_zone:
            valid_zones.append((left_zone_min, left_zone_max))
        if valid_mid_left_zone:
            valid_zones.append((mid_left_zone_min, mid_left_zone_max))
        if valid_mid_right_zone:
            valid_zones.append((mid_right_zone_min, mid_right_zone_max))
        if valid_right_zone:
            valid_zones.append((right_zone_min, right_zone_max))

        # Choose a zone and position green ball
        if valid_zones:
            chosen_zone = rng.choice(valid_zones)
            green_ball_x = rng.uniform(chosen_zone[0], chosen_zone[1])
            valid_level_found = True
        else:
            print("No valid zones found, trying again")

    # Always place green ball at the top of the environment
    green_ball_y = 5 - green_ball_radius - 0.1  # Just below the top boundary

    floor = Bar(
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

    blue_platform = Bar(
        x=blue_platform_x,
        y=blue_platform_y,
        length=blue_platform_length,
        angle=0.0,
        color="blue",
        dynamic=True,
    )

    # Create barriers and green ball
    left_barrier = Bar(
        x=left_barrier_x,
        y=barrier_y,
        length=barrier_length,
        angle=90.0,
        color="black",
        dynamic=False,
    )

    right_barrier = Bar(
        x=right_barrier_x,
        y=barrier_y,
        length=barrier_length,
        angle=-90.0,
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

    # Red ball placement - ensure it's above the floor
    red_ball_radius = rng.uniform(0.2, 0.8)  # Reduced max size to avoid issues
    red_ball_y = max(-4.9, floor_y + red_ball_radius + 0.1)  # Ensure above floor

    # Find a clear spot for the red ball
    red_ball_x_candidates = []
    for x in np.linspace(-4.5 + red_ball_radius, 4.5 - red_ball_radius, 20):
        # Check for overlaps with other objects (simplified)
        if (
            abs(x - black_ball_x) > (black_ball_radius + red_ball_radius + 0.1)
            and abs(x - green_ball_x) > (green_ball_radius + red_ball_radius + 0.1)
            and abs(x - left_barrier_x)
            > (barrier_thickness / 2 + red_ball_radius + 0.1)
            and abs(x - right_barrier_x)
            > (barrier_thickness / 2 + red_ball_radius + 0.1)
        ):
            red_ball_x_candidates.append(x)

    if red_ball_x_candidates:
        red_ball_x = rng.choice(red_ball_x_candidates)
    else:
        # Fallback position
        red_ball_x = rng.uniform(-4.5 + red_ball_radius, 4.5 - red_ball_radius)

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
