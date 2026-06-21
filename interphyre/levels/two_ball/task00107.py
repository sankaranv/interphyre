import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_ground", success_time
    )


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    gap_options = np.linspace(0.15, 0.3, 4)
    lower_y_options = np.linspace(0.2, 0.3, 3)
    mid_y_options = np.linspace(0.45, 0.55, 3)
    mid_length_options = np.linspace(0.15, 0.3, 4)

    gap_frac = rng.choice(gap_options)
    lower_y = rng.choice(lower_y_options)
    mid_y = rng.choice(mid_y_options)
    mid_length_frac = rng.choice(mid_length_options)

    bar_thickness = 0.2
    lower_y_world = (-5.0) + lower_y * (10.0)
    gap_width = gap_frac * (10.0)
    gap_left = -gap_width / 2
    gap_right = gap_width / 2

    left_lower = Bar(
        left=(-5.0),
        right=gap_left,
        y=lower_y_world + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_lower = Bar(
        left=gap_right,
        right=(5.0),
        y=lower_y_world + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    blocker_length = 0.02 * (10.0)
    left_blocker = Bar(
        top=left_lower.top + blocker_length,
        bottom=left_lower.top,
        x=left_lower.right,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_blocker = Bar(
        top=right_lower.top + blocker_length,
        bottom=right_lower.top,
        x=right_lower.left,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    mid_length = mid_length_frac * (10.0)
    mid_bar = Bar(
        left=-mid_length / 2,
        right=mid_length / 2,
        y=(-5.0) + mid_y * (10.0) + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    ball_radius = 0.1 * (10.0) / 2
    green_ball_x = 0.0
    green_ball_y = (-5.0) + 0.9 * (10.0) + ball_radius
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    purple_ground = Bar(
        left=(-5.0),
        right=(5.0),
        y=(-5.0) + bar_thickness / 2,
        thickness=bar_thickness,
        color="purple",
        dynamic=False,
    )

    red_ball_1 = Ball(
        x=-3.0,
        y=4.0,
        radius=0.5,
        color="red",
        dynamic=True,
    )
    red_ball_2 = Ball(
        x=3.0,
        y=4.0,
        radius=0.5,
        color="red",
        dynamic=True,
    )

    objects = {
        "green_ball": green_ball,
        "mid_bar": mid_bar,
        "purple_ground": purple_ground,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }
    objects["left_lower"] = left_lower
    objects["right_lower"] = right_lower
    objects["left_blocker"] = left_blocker
    objects["right_blocker"] = right_blocker

    return Level(
        name="task00107",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball to the purple ground."},
    )
