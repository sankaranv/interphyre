import numpy as np
from phyre2.objects import Ball, Platform, PhyreObject
from phyre2.level import Level
from typing import cast
from phyre2.levels import register_level


def success_condition(engine):
    return engine.has_contact("green_ball", "blue_platform")


def build_level(seed=None):
    rng = np.random.default_rng(seed)

    # Floor placement (keeping within bounds)
    floor_y = rng.uniform(-4.5, 2.5)
    floor = Platform(
        x=0.0,
        y=floor_y,
        length=10.0,
        angle=0.0,
        color="black",
        dynamic=False,
    )

    # Black ball placement
    black_ball_radius = 0.4
    black_ball_x = rng.uniform(-4.5 + black_ball_radius, 4.5 - black_ball_radius)
    black_ball = Ball(
        x=black_ball_x,
        y=floor_y + black_ball_radius + 0.1,
        radius=black_ball_radius,
        color="black",
        dynamic=False,
    )

    # Blue platform placement
    blue_platform_length = rng.uniform(
        3, min(5.5, 10 - 2 * black_ball_radius)
    )  # Ensure it fits
    platform_thickness = 0.2  # Default thickness

    # Position blue platform centered directly above the black ball
    blue_platform_y = (floor_y + 2 * black_ball_radius + 0.1) + (platform_thickness / 2)
    blue_platform_x = black_ball_x  # Center directly above the black ball

    blue_platform = Platform(
        x=blue_platform_x,
        y=blue_platform_y,
        length=blue_platform_length,
        angle=0.0,
        color="blue",
        dynamic=True,
    )

    # Calculate platform edges
    platform_left = blue_platform_x - blue_platform_length / 2
    platform_right = blue_platform_x + blue_platform_length / 2

    # Minimum clearance for all objects
    min_clearance = 0.2
    barrier_thickness = 0.2  # Default thickness for barriers

    # Barrier position calculation first (so we can position green ball with proper clearance)
    # Calculate positions that respect minimum clearance from blue platform
    left_barrier_max_x = platform_left - min_clearance - (barrier_thickness / 2)
    right_barrier_min_x = platform_right + min_clearance + (barrier_thickness / 2)

    # Ensure these positions are within bounds
    left_barrier_max_x = max(-4.9, min(left_barrier_max_x, -0.5))
    right_barrier_min_x = min(4.9, max(right_barrier_min_x, 0.5))

    # Determine reasonable barrier x-positions
    left_barrier_x = (
        rng.uniform(-4.9, left_barrier_max_x) if left_barrier_max_x > -4.9 else -4.0
    )
    right_barrier_x = (
        rng.uniform(right_barrier_min_x, 4.9) if right_barrier_min_x < 4.9 else 4.0
    )

    # Green ball placement - accounting for clearance from barriers
    green_ball_radius = 0.4

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
        right_barrier_x - (barrier_thickness / 2) - green_ball_radius - min_clearance
    )
    mid_right_zone_min = platform_right + green_ball_radius + min_clearance
    valid_mid_right_zone = mid_right_zone_min < mid_right_zone_max

    # Zone to the right of right barrier
    right_zone_max = 5 - green_ball_radius - 0.1
    right_zone_min = (
        right_barrier_x + (barrier_thickness / 2) + green_ball_radius + min_clearance
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
    else:
        # Emergency fallback - place in center with barriers adjusted later
        green_ball_x = 0
        # Adjust barriers to make room
        left_barrier_x = -4.5
        right_barrier_x = 4.5

    # Always place green ball at the top of the environment
    green_ball_y = 5 - green_ball_radius - 0.1  # Just below the top boundary

    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    # Ensure barrier height and length are valid
    barrier_y = rng.uniform(floor_y + 0.5, 4.5)
    max_possible_length = min(4.9 - barrier_y, barrier_y - floor_y)

    if max_possible_length >= 1:
        barrier_length = rng.uniform(1, max_possible_length)
    else:
        barrier_length = max(
            0.2, max_possible_length
        )  # Use whatever space is available, minimum 0.2

    # Create barriers
    left_barrier = Platform(
        x=left_barrier_x,
        y=barrier_y,
        length=barrier_length,
        angle=90.0,
        color="black",
        dynamic=False,
    )

    right_barrier = Platform(
        x=right_barrier_x,
        y=barrier_y,
        length=barrier_length,
        angle=-90.0,
        color="black",
        dynamic=False,
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
        target_object="green_ball",
        goal_object="blue_platform",
        success_condition=success_condition,
        metadata={"description": "Make sure the green ball is touching the blue bar"},
    )


register_level("seesaw")(build_level)
