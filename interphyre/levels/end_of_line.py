import numpy as np
from interphyre.objects import Ball, Bar, PhyreObject
from interphyre.level import Level
from typing import cast
from interphyre.levels import register_level
from interphyre.render import WORLD_WIDTH, MIN_Y


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "purple_wall", success_time)


@register_level
def build_level(seed=None):
    rng = np.random.default_rng(seed)

    purple_wall_x = rng.choice([-4.9, 4.9])
    purple_wall = Bar(
        top=5.0,
        bottom=-5.0,
        x=purple_wall_x,
        thickness=0.2,
        color="purple",
        dynamic=False,
    )

    green_ball_radius = rng.uniform(0.2, 0.6)
    bar_thickness = 0.2
    table_height = rng.uniform(0.5, 1.0)
    table_angle = 60.0
    table_length = (
        WORLD_WIDTH
        - 4 * green_ball_radius
        - 2 * table_height / np.tan(np.radians(table_angle))
        - bar_thickness
    )
    angle_rad = np.radians(table_angle)
    # Buffer to extend table top slightly beyond leg positions
    buffer = 0.1

    table_top_left = -(table_length + buffer * 2) / 2
    table_top_right = (table_length + buffer * 2) / 2
    table_top = Bar(
        left=table_top_left,
        right=table_top_right,
        y=MIN_Y + table_height,
        thickness=0.2,
        color="black",
        dynamic=False,
    )

    left_leg_top_x = table_top_left + bar_thickness / 4
    left_leg_top_y = MIN_Y + table_height
    left_leg_bottom_x = left_leg_top_x - table_height / np.tan(angle_rad)
    left_leg_bottom_y = MIN_Y

    right_leg_top_x = table_top_right - bar_thickness / 4
    right_leg_top_y = MIN_Y + table_height
    right_leg_bottom_x = right_leg_top_x + table_height / np.tan(angle_rad)
    right_leg_bottom_y = MIN_Y

    table_left_leg = Bar.from_endpoints(
        x1=left_leg_top_x,
        y1=left_leg_top_y,
        x2=left_leg_bottom_x,
        y2=left_leg_bottom_y,
        thickness=0.2,
        color="black",
        dynamic=False,
    )

    table_right_leg = Bar.from_endpoints(
        x1=right_leg_top_x,
        y1=right_leg_top_y,
        x2=right_leg_bottom_x,
        y2=right_leg_bottom_y,
        thickness=0.2,
        color="black",
        dynamic=False,
    )

    # Add a little extra length to the legs to make the connections look cleaner
    table_left_leg.length += bar_thickness / 2
    table_right_leg.length += bar_thickness / 2

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

    red_ball_radius = rng.uniform(0.2, 1)
    red_ball = Ball(
        x=-3,
        y=rng.uniform(-1 - table_height, 2 - table_height),
        radius=red_ball_radius,
        color="red",
        dynamic=True,
    )

    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "purple_wall": purple_wall,
        "table_top": table_top,
        "table_left_leg": table_left_leg,
        "table_right_leg": table_right_leg,
    }

    return Level(
        name="end_of_line",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Knock the green ball off the table so it hits the purple wall"
        },
    )
