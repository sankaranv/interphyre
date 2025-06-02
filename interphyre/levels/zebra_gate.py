import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.render import MAX_X, MAX_Y, MIN_X, MIN_Y


def success_condition(engine):
    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "purple_pad", success_time)


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    purple_pad_length = rng.uniform(3, 5)
    purple_pad_x = rng.choice(
        [
            MIN_X + purple_pad_length / 2,
            MAX_X - purple_pad_length / 2,
        ]
    )
    purple_pad = Bar(
        x=purple_pad_x,
        y=-4.9,
        length=purple_pad_length,
        angle=0,
        color="purple",
        dynamic=False,
    )

    gap_point = rng.uniform(-3, 3)
    gap_width = rng.uniform(1, 2)

    gap_bottom = gap_point - gap_width / 2
    gap_top = gap_point + gap_width / 2

    divider_x = purple_pad_x + (purple_pad_length / 2 + 0.1) * np.sign(-purple_pad_x)

    top_divider_length = MAX_Y - gap_top
    top_divider_y = gap_top + top_divider_length / 2
    top_divider = Bar(
        x=divider_x,
        y=top_divider_y,
        length=top_divider_length,
        angle=90,
        color="black",
        dynamic=False,
    )

    bottom_divider_length = gap_bottom - MIN_Y
    bottom_divider_y = MIN_Y + bottom_divider_length / 2
    bottom_divider = Bar(
        x=divider_x,
        y=bottom_divider_y,
        length=bottom_divider_length,
        angle=90,
        color="black",
        dynamic=False,
    )

    if purple_pad_x < 0:
        available_width = MAX_X - (divider_x + 0.1)
        slat_x = (divider_x + 0.1) + available_width / 2
    else:
        available_width = (divider_x - 0.1) - MIN_X
        slat_x = MIN_X + available_width / 2

    slat_length = 0.5 * available_width
    slat_angle = rng.uniform(10, 40) * np.sign(-purple_pad_x)
    slat_y_positions = np.linspace(-4.5, 4.5, 7)

    slat_1 = Bar(
        x=slat_x,
        y=slat_y_positions[0],
        length=slat_length,
        angle=slat_angle,
        color="black",
        dynamic=False,
    )
    slat_2 = Bar(
        x=slat_x,
        y=slat_y_positions[1],
        length=slat_length,
        angle=slat_angle,
        color="black",
        dynamic=False,
    )
    slat_3 = Bar(
        x=slat_x,
        y=slat_y_positions[2],
        length=slat_length,
        angle=slat_angle,
        color="black",
        dynamic=False,
    )
    slat_4 = Bar(
        x=slat_x,
        y=slat_y_positions[3],
        length=slat_length,
        angle=slat_angle,
        color="black",
        dynamic=False,
    )
    slat_5 = Bar(
        x=slat_x,
        y=slat_y_positions[4],
        length=slat_length,
        angle=slat_angle,
        color="black",
        dynamic=False,
    )
    slat_6 = Bar(
        x=slat_x,
        y=slat_y_positions[5],
        length=slat_length,
        angle=slat_angle,
        color="black",
        dynamic=False,
    )
    slat_7 = Bar(
        x=slat_x,
        y=slat_y_positions[6],
        length=slat_length,
        angle=slat_angle,
        color="black",
        dynamic=False,
    )

    # Calculate available space accounting for angled slats and divider thickness
    if purple_pad_x < 0:
        # Slats tilt clockwise, so their leftmost point varies by y-position
        # For safety, use the most restrictive case (where slat extends furthest left)
        slat_left_extension = (slat_length / 2) * np.cos(np.radians(slat_angle))
        slat_leftmost_x = slat_x - slat_left_extension
        space_width = slat_leftmost_x - (divider_x + 0.1)
        space_center_x = (divider_x + 0.1) + space_width / 2
    else:
        # Slats tilt counterclockwise, so their rightmost point varies by y-position
        slat_right_extension = (slat_length / 2) * abs(np.cos(np.radians(slat_angle)))
        slat_rightmost_x = slat_x + slat_right_extension
        space_width = (divider_x - 0.1) - slat_rightmost_x
        space_center_x = slat_rightmost_x + space_width / 2

    max_radius = min(space_width / 2, (gap_width / 2) - 0.05)
    green_ball_radius = max_radius if max_radius < 0.2 else rng.uniform(0.2, max_radius)
    green_ball_min_x = space_center_x - (space_width / 2 - green_ball_radius)
    green_ball_max_x = space_center_x + (space_width / 2 - green_ball_radius)
    green_ball_x = rng.uniform(green_ball_min_x, green_ball_max_x)

    green_ball_y = rng.uniform(4.7, 4.9)
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    red_ball = Ball(
        x=0,
        y=-4.5,
        radius=rng.uniform(0.3, 0.6),
        color="red",
        dynamic=True,
    )

    # Gray ball on the opposite side of the divider from the green ball
    gray_ball_radius = 0.5
    gray_ball_offset = 0.2
    gray_ball_min_height = 2
    if purple_pad_x < 0:
        gray_ball_x = divider_x - gray_ball_offset - gray_ball_radius
    else:
        gray_ball_x = divider_x + gray_ball_offset + gray_ball_radius

    min_y_from_ground = -4.9 + gray_ball_min_height + gray_ball_radius
    max_y = 4.5 - gray_ball_radius

    # Available y ranges avoiding the gap
    gap_bottom = gap_point - gap_width / 2
    gap_top = gap_point + gap_width / 2
    below_gap_min = min_y_from_ground
    below_gap_max = gap_bottom - gray_ball_radius
    above_gap_min = gap_top + gray_ball_radius
    above_gap_max = max_y
    below_gap_valid = below_gap_max > below_gap_min
    above_gap_valid = above_gap_max > above_gap_min

    if below_gap_valid and above_gap_valid:
        # Both regions available, choose randomly
        if rng.random() < 0.5:
            gray_ball_y = rng.uniform(below_gap_min, below_gap_max)
        else:
            gray_ball_y = rng.uniform(above_gap_min, above_gap_max)
    elif below_gap_valid:
        gray_ball_y = rng.uniform(below_gap_min, below_gap_max)
    elif above_gap_valid:
        gray_ball_y = rng.uniform(above_gap_min, above_gap_max)
    else:
        gray_ball_y = 0

    gray_ball = Ball(
        x=gray_ball_x,
        y=gray_ball_y,
        radius=gray_ball_radius,
        color="gray",
        dynamic=True,
    )

    objects = {
        "purple_pad": purple_pad,
        "top_divider": top_divider,
        "bottom_divider": bottom_divider,
        "green_ball": green_ball,
        "red_ball": red_ball,
        "gray_ball": gray_ball,
        "slat_1": slat_1,
        "slat_2": slat_2,
        "slat_3": slat_3,
        "slat_4": slat_4,
        "slat_5": slat_5,
        "slat_6": slat_6,
        "slat_7": slat_7,
    }

    return Level(
        name="zebra_gate",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Get the green ball through the gap and onto the purple pad.",
        },
    )
