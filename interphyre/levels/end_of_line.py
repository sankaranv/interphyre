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
def build_level(seed=None) -> Level:
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

    # Calculate table length
    leg_extension = table_height / np.tan(np.radians(table_angle))
    table_length = (
        WORLD_WIDTH - 4 * green_ball_radius - 2 * leg_extension - bar_thickness
    )

    # Buffer to extend table top slightly beyond leg positions
    buffer = 0.1
    table_top_length = table_length + buffer * 2
    table_top_y = MIN_Y + table_height

    table_top = Bar.from_point_and_angle(
        x=0,
        y=table_top_y,
        length=table_top_length,
        angle=0,
        thickness=0.2,
        color="black",
        dynamic=False,
    )

    # Create table legs as ramps from the table edges
    leg_length = table_height / np.sin(np.radians(table_angle))

    table_left_leg = Bar.from_corner(
        corner_x=table_top.left + bar_thickness / 4,
        corner_y=table_top.y,
        angle=180 + table_angle,
        length=leg_length,
        thickness=0.2,
        color="black",
        dynamic=False,
    )

    table_right_leg = Bar.from_corner(
        corner_x=table_top.right - bar_thickness / 4,
        corner_y=table_top.y,
        angle=-table_angle,
        length=leg_length,
        thickness=0.2,
        color="black",
        dynamic=False,
    )

    # Add a little extra length to the legs to make the connections look cleaner
    table_left_leg.length += bar_thickness / 2
    table_right_leg.length += bar_thickness / 2

    # Position green ball on table, ensuring it's not too close to target wall
    green_ball_x = rng.uniform(
        -table_length / 2 + green_ball_radius + 0.5,
        table_length / 2 - green_ball_radius - 0.5,
    )
    # Ensure green ball is not already near the target wall
    if abs(green_ball_x - purple_wall_x) < 2.0:
        # Place on opposite side
        green_ball_x = -green_ball_x

    green_ball = Ball(
        x=green_ball_x,
        y=table_top_y + green_ball_radius + 0.1,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    # Position red ball away from target wall to avoid trivial solutions
    red_ball_radius = rng.uniform(0.2, 1)
    if purple_wall_x < 0:
        # Wall on left, place red ball on right side
        red_ball_x = rng.uniform(0, 4.5)
    else:
        # Wall on right, place red ball on left side
        red_ball_x = rng.uniform(-4.5, 0)

    red_ball = Ball(
        x=red_ball_x,
        y=rng.uniform(table_top_y + 1, 4.5),
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
