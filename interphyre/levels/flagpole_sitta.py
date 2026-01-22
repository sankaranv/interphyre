import numpy as np
from interphyre.objects import Ball, Bar, PhyreObject
from interphyre.level import Level
from typing import cast
from interphyre.levels import register_level
from interphyre.config import MIN_X, MIN_Y, MAX_X


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

    ramp_offset = round(rng.uniform(1, 2), 2)
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

    left_ramp_max_x = MIN_X + ramp_length * np.cos(np.radians(315))
    right_ramp_min_x = MAX_X + ramp_length * np.cos(np.radians(225))

    buffer = 1.0
    min_flagpole_x = left_ramp_max_x + buffer
    max_flagpole_x = right_ramp_min_x - buffer

    if min_flagpole_x >= max_flagpole_x:
        center = (MIN_X + MAX_X) / 2
        min_flagpole_x = center - 1.0
        max_flagpole_x = center + 1.0

    flagpole_x = round(rng.uniform(min_flagpole_x, max_flagpole_x), 2)
    flagpole_length = round(rng.uniform(3, 7), 2)
    flagpole_y = round(
        purple_ground.y + purple_ground.thickness / 2 + flagpole_length / 2, 2
    )
    flagpole = Bar.from_point_and_angle(
        x=flagpole_x,
        y=flagpole_y,
        angle=90.0,
        length=flagpole_length,
        thickness=0.2,
        color="gray",
        friction=1.2,
        restitution=0.1,
        linear_damping=2.0,
        angular_damping=3.0,
        density=2.0,
        dynamic=True,
    )

    green_ball_radius = round(rng.uniform(0.5, 1.0), 2)
    green_ball_x = flagpole.x
    green_ball_y = round(
        flagpole.y
        + (flagpole.length / 2)
        + green_ball_radius
        - 0.01 * green_ball_radius,
        3,
    )
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        friction=0.8,
        restitution=0.5,
        linear_damping=1.0,
        angular_damping=1.0,
        dynamic=True,
    )

    red_ball_radius = round(rng.uniform(0.2, 0.7), 2)
    red_ball_offset = round(rng.uniform(1.5, 3.0), 2)
    red_ball_x = flagpole.x + rng.choice([-1, 1]) * red_ball_offset
    red_ball_y = flagpole.top + red_ball_radius
    red_ball = Ball(
        x=red_ball_x,
        y=red_ball_y,
        radius=red_ball_radius,
        color="red",
        dynamic=True,
    )

    # Ceiling very close to ball to prevent trivial falling (like PHYRE reference)
    # eps = 0.01 * scene_height in PHYRE, which is ~0.1 in our coordinates
    ceiling_clearance = 0.1
    ceiling = Bar.from_point_and_angle(
        x=0.0,
        y=green_ball_y + green_ball_radius + ceiling_clearance,
        length=10.0,
        thickness=0.2,
        angle=0.0,
        color="black",
        dynamic=False,
    )

    objects = {
        "flagpole": flagpole,
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
