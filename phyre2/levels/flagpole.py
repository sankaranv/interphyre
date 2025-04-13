import numpy as np
from phyre2.objects import Ball, Platform, PhyreObject
from phyre2.level import Level
from typing import cast
from phyre2.levels import register_level


def success_condition(engine):
    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_ground", success_time
    )


def build_level(seed=None):
    rng = np.random.default_rng(seed)

    purple_ground = Platform(
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
    flagpole = Platform(
        x=flagpole_x,
        y=flagpole_y,
        length=flagpole_length,
        thickness=0.2,
        angle=90.0,
        color="gray",
        friction=0.8,
        dynamic=True,
    )

    green_ball_radius = rng.uniform(0.5, 1.0)
    green_ball_x = flagpole_x
    green_ball_y = flagpole_y + flagpole_length / 2 + green_ball_radius
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        friction=0.8,
        dynamic=True,
    )

    red_ball_radius = rng.uniform(0.2, 0.7)
    red_ball_x = flagpole_x
    red_ball_y = flagpole_y + flagpole_length / 2 + red_ball_radius
    red_ball = Ball(
        x=red_ball_x,
        y=red_ball_y,
        radius=red_ball_radius,
        color="red",
        dynamic=True,
    )

    ceiling_clearance = 0.2
    ceiling = Platform(
        x=0.0,
        y=green_ball_y + green_ball_radius + ceiling_clearance,
        length=10.0,
        thickness=0.2,
        angle=0.0,
        color="black",
        dynamic=False,
    )

    ramp_offset = rng.uniform(1, 2)
    ramp_angle = 45  # 45 degrees angle

    # Wall thickness
    wall_thickness = 0.2

    # Calculate ramp length using trigonometry
    ramp_length = round(ramp_offset / np.cos(np.radians(ramp_angle)), 2)

    # Left ramp
    # Position calculations accounting for wall thickness
    left_ramp_x = -5 + ramp_offset / 2 + wall_thickness / 2
    left_ramp_y = -5 + ramp_offset / 2 + wall_thickness + 0.1

    left_ramp = Platform(
        x=left_ramp_x,
        y=left_ramp_y,
        length=ramp_length,
        thickness=wall_thickness,
        angle=-ramp_angle,  # Negative angle for left ramp (pointing up and right)
        color="black",
        dynamic=False,
    )

    # Right ramp
    # Position calculations accounting for wall thickness
    right_ramp_x = 5 - ramp_offset / 2 - wall_thickness / 2
    right_ramp_y = -5 + ramp_offset / 2 + wall_thickness / 2 + 0.1

    right_ramp = Platform(
        x=right_ramp_x,
        y=right_ramp_y,
        length=ramp_length,
        thickness=wall_thickness,
        angle=ramp_angle,  # Positive angle for right ramp (pointing up and left)
        color="black",
        dynamic=False,
    )

    # Assemble objects dictionary.
    objects = {
        "purple_ground": purple_ground,
        "flagpole": flagpole,
        "green_ball": green_ball,
        "red_ball": red_ball,
        "ceiling": ceiling,
        "left_ramp": left_ramp,
        "right_ramp": right_ramp,
    }

    return Level(
        name="flagpole",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Knock the green ball off of the pole and onto the ground"
        },
    )


register_level("flagpole")(build_level)
