import numpy as np
from interphyre.objects import Ball, Bar, PhyreObject
from interphyre.level import Level
from typing import cast
from interphyre.levels import register_level
from interphyre.render import MIN_X, MIN_Y, MAX_X


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_ground", success_time
    )


@register_level
def build_level(seed=None):
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

    flagpole_x = rng.uniform(-4, 4)
    flagpole_length = rng.uniform(3, 7)
    flagpole_y = purple_ground.y + purple_ground.thickness / 2 + flagpole_length / 2
    flagpole = Bar.from_point_and_angle(
        x=flagpole_x,
        y=flagpole_y,
        angle=90.0,
        length=flagpole_length,
        thickness=0.2,
        color="gray",
        friction=0.5,  # Use default friction
        dynamic=True,
    )

    # Add a wider platform on top of the flagpole for better ball stability
    platform_length = rng.uniform(1.5, 2.5)  # Wider platform for better stability
    platform = Bar.from_point_and_angle(
        x=flagpole_x,
        y=flagpole.top + 0.1,  # Slightly above flagpole top
        angle=0.0,
        length=platform_length,
        thickness=0.2,  # Slightly thicker for stability
        color="gray",
        friction=0.5,
        dynamic=False,  # Make platform static for better stability
    )

    green_ball_radius = rng.uniform(0.5, 1.0)
    # Position green ball on the platform for better stability
    green_ball_x = platform.x
    green_ball_y = platform.y + platform.thickness / 2 + green_ball_radius + 0.05  # Slightly higher for better contact
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        friction=0.5,  # Use default friction
        dynamic=True,
    )

    # Add small side barriers to help keep the ball on the platform
    barrier_height = 0.3
    left_barrier = Bar.from_point_and_angle(
        x=platform.x - platform.length / 2 - 0.1,
        y=platform.y + platform.thickness / 2 + barrier_height / 2,
        angle=0.0,
        length=barrier_height,
        thickness=0.1,
        color="gray",
        friction=0.5,
        dynamic=False,  # Make barriers static for better stability
    )
    
    right_barrier = Bar.from_point_and_angle(
        x=platform.x + platform.length / 2 + 0.1,
        y=platform.y + platform.thickness / 2 + barrier_height / 2,
        angle=0.0,
        length=barrier_height,
        thickness=0.1,
        color="gray",
        friction=0.5,
        dynamic=False,  # Make barriers static for better stability
    )

    red_ball_radius = rng.uniform(0.2, 0.7)
    # Position red ball to the side of the flagpole, not overlapping
    red_ball_offset = rng.uniform(1.5, 3.0)  # Distance from flagpole
    red_ball_x = flagpole.x + rng.choice([-1, 1]) * red_ball_offset
    red_ball_y = flagpole.top + red_ball_radius
    red_ball = Ball(
        x=red_ball_x,
        y=red_ball_y,
        radius=red_ball_radius,
        color="red",
        dynamic=True,
    )

    ceiling_clearance = 0.2
    ceiling = Bar.from_point_and_angle(
        x=0.0,
        y=green_ball_y + green_ball_radius + ceiling_clearance,
        length=10.0,
        thickness=0.2,
        angle=0.0,
        color="black",
        dynamic=False,
    )

    ramp_offset = rng.uniform(1, 2)
    wall_thickness = 0.2
    ramp_length = ramp_offset * np.sqrt(2)

    left_corner_y = MIN_Y + ramp_offset + wall_thickness / 2
    right_corner_y = MIN_Y + ramp_offset + wall_thickness / 2

    left_ramp = Bar.from_corner(
        corner_x=MIN_X,
        corner_y=left_corner_y,
        angle=315,
        length=ramp_length,
        thickness=wall_thickness,
        color="black",
        dynamic=False,
    )

    right_ramp = Bar.from_corner(
        corner_x=MAX_X,
        corner_y=right_corner_y,
        angle=225,
        length=ramp_length,
        thickness=wall_thickness,
        color="black",
        dynamic=False,
    )

    objects = {
        "flagpole": flagpole,
        "platform": platform,
        "left_barrier": left_barrier,
        "right_barrier": right_barrier,
        "green_ball": green_ball,
        "red_ball": red_ball,
        "ceiling": ceiling,
        "left_ramp": left_ramp,
        "right_ramp": right_ramp,
        "purple_ground": purple_ground,
    }

    return Level(
        name="flagpole_sitta",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Knock the green ball off of the pole and onto the ground"
        },
    )
