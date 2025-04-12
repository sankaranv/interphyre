import numpy as np
from phyre2.objects import Ball, Platform, PhyreObject
from phyre2.level import Level
from typing import cast
from phyre2.levels import register_level


def success_condition(engine):
    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "purple_wall", success_time)


def build_level(seed=None):
    rng = np.random.default_rng(seed)

    purple_wall = Platform(
        x=rng.choice([-4.9, 4.9]),
        y=0.0,
        length=10.0,
        thickness=0.2,
        angle=90.0,
        color="purple",
        dynamic=False,
    )

    table_length = rng.uniform(3, 7)
    table_height = rng.uniform(0.5, 1.5)
    table_angle = 60.0
    angle_rad = np.radians(table_angle)
    ground_level = -5
    # Adjust buffer to increase length of the table top to match the leg position
    buffer = 0.1
    leg_length = table_height / np.sin(angle_rad)
    leg_pos_x = table_length / 2 + np.cos(angle_rad) * leg_length / 2
    leg_pos_y = ground_level + (leg_length * np.sin(angle_rad)) / 2

    table_top = Platform(
        x=0.0,
        y=ground_level + table_height,
        length=table_length + buffer * 2,
        thickness=0.2,
        angle=0.0,
        color="black",
        dynamic=False,
    )

    table_left_leg = Platform(
        x=-leg_pos_x - buffer / 2,
        y=leg_pos_y,
        length=leg_length + buffer,
        thickness=0.2,
        angle=table_angle,
        color="black",
        dynamic=False,
    )

    table_right_leg = Platform(
        x=leg_pos_x + buffer / 2,
        y=leg_pos_y,
        length=leg_length + buffer,
        thickness=0.2,
        angle=-table_angle,
        color="black",
        dynamic=False,
    )

    green_ball_radius = rng.uniform(0.2, 0.6)
    red_ball_radius = rng.uniform(0.2, 1)

    green_ball = Ball(
        x=rng.uniform(
            -table_length / 2 + green_ball_radius + 0.5,
            table_length / 2 - green_ball_radius - 0.5,
        ),
        y=rng.uniform(-1 - table_height, 2 - table_height),
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    red_ball = Ball(
        x=-3,
        y=rng.uniform(-1 - table_height, 2 - table_height),
        radius=red_ball_radius,
        color="red",
        dynamic=True,
    )

    # Avoid trivial solutions

    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "purple_wall": purple_wall,
        "table_top": table_top,
        "table_left_leg": table_left_leg,
        "table_right_leg": table_right_leg,
    }

    return Level(
        name="knock_ball_off_table",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Knock the green ball off the table to the purple wall"
        },
    )


register_level("knock_ball_off_table")(build_level)
