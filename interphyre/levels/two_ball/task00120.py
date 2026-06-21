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

    bar_thickness = 0.2
    ball_radius = 0.07 * (10.0) / 2
    ball_top = (-5.0) + 0.93 * (10.0)
    green_ball_x = (-5.0) + rng.uniform(0.2, 0.8) * (10.0)
    green_ball_y = ball_top - ball_radius
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    objects = {
        "green_ball": green_ball,
    }

    bar_count = rng.integers(7, 9)
    cap_length = 0.08 * (10.0)
    bar_lengths = [1.4, 1.9, 2.4, 2.9]
    center_x_options = [-3.2, -1.8, -0.4, 0.8, 2.2, 3.2]
    y_positions = np.linspace(
        0.15,
        (ball_top - 2 * ball_radius - (-5.0)) / (10.0),
        bar_count,
    )
    for idx, y_frac in enumerate(reversed(y_positions)):
        bar_length = rng.choice(bar_lengths)
        center_x = green_ball_x if idx == 0 else rng.choice(center_x_options)
        bar_y = (-5.0) + (y_frac + rng.normal() * 0.015) * (10.0)
        bar = Bar(
            left=center_x - bar_length / 2,
            right=center_x + bar_length / 2,
            y=bar_y,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )
        objects[f"bar_{idx}"] = bar

        left_cap = Bar(
            top=bar.top + cap_length,
            bottom=bar.top,
            x=bar.left,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )
        right_cap = Bar(
            top=bar.top + cap_length,
            bottom=bar.top,
            x=bar.right,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )
        objects[f"bar_{idx}_left_cap"] = left_cap
        objects[f"bar_{idx}_right_cap"] = right_cap

    lower_bar_length = 2.0 * (10.0) / 5
    lower_bar = Bar(
        left=(-5.0) + 0.35 * (10.0),
        right=(-5.0) + 0.35 * (10.0) + lower_bar_length,
        y=(-5.0) + 0.12 * (10.0) + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    objects["lower_bar"] = lower_bar

    pair_length = 0.2 * (10.0)
    pair_y = (-5.0) + 0.25 * (10.0)
    pair_top = Bar(
        left=(5.0) - 0.35 * (10.0),
        right=(5.0) - 0.35 * (10.0) + pair_length,
        y=pair_y + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    pair_bottom = Bar(
        left=pair_top.left + 0.03 * (10.0),
        right=pair_top.right - 0.03 * (10.0),
        y=pair_y - 0.07 * (10.0) + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    objects["pair_top"] = pair_top
    objects["pair_bottom"] = pair_bottom

    trap_length = 0.15 * (10.0)
    left_trap = Bar.from_point_and_angle(
        x=(-5.0) + trap_length / 2,
        y=(-5.0) + bar_thickness / 2,
        angle=10.0,
        length=trap_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_trap = Bar.from_point_and_angle(
        x=(5.0) - trap_length / 2,
        y=(-5.0) + bar_thickness / 2,
        angle=-10.0,
        length=trap_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    ground_length = right_trap.left - left_trap.right
    ground_x = (right_trap.left + left_trap.right) / 2
    purple_ground = Bar.from_point_and_angle(
        x=ground_x,
        y=(-5.0) + bar_thickness / 2,
        length=ground_length,
        angle=0.0,
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

    objects.update(
        {
            "left_trap": left_trap,
            "right_trap": right_trap,
            "purple_ground": purple_ground,
            "red_ball_1": red_ball_1,
            "red_ball_2": red_ball_2,
        }
    )

    return Level(
        name="task00120",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball to the purple ground."},
    )
