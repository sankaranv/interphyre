import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.levels.two_ball._constants import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_ground", success_time
    )


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    bar_thickness = 0.2
    ball_radius = 0.07 * WORLD_WIDTH / 2
    ball_top = MIN_Y + 0.93 * WORLD_HEIGHT
    green_ball_x = rng.uniform(MIN_X + 2.0, MAX_X - 2.0)
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

    bar_count = rng.integers(5, 7)
    cap_length = 0.08 * WORLD_HEIGHT
    bar_lengths = [1.4, 1.8, 2.2]
    center_x_options = [-3.2, -1.8, -0.4, 0.8, 2.2, 3.2]
    y_options = [0.7, 0.6, 0.5, 0.4, 0.3, 0.22]
    chosen_y = rng.choice(y_options, size=bar_count, replace=False)

    for i, y_frac in enumerate(sorted(chosen_y, reverse=True)):
        bar_y = MIN_Y + y_frac * WORLD_HEIGHT
        bar_length = rng.choice(bar_lengths)
        center_x = green_ball_x if i == 0 else rng.choice(center_x_options)
        bar = Bar(
            left=center_x - bar_length / 2,
            right=center_x + bar_length / 2,
            y=bar_y,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )
        objects[f"bar_{i}"] = bar

        right_cap = Bar(
            top=bar.top + cap_length,
            bottom=bar.top,
            x=bar.right,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )
        objects[f"bar_{i}_right_cap"] = right_cap
        if rng.uniform() < 0.35:
            left_cap = Bar(
                top=bar.top + cap_length,
                bottom=bar.top,
                x=bar.left,
                thickness=bar_thickness,
                color="black",
                dynamic=False,
            )
            objects[f"bar_{i}_left_cap"] = left_cap

    trap_length = 0.15 * WORLD_WIDTH
    left_trap = Bar.from_point_and_angle(
        x=MIN_X + trap_length / 2,
        y=MIN_Y + bar_thickness / 2,
        length=trap_length,
        angle=10.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_trap = Bar.from_point_and_angle(
        x=MAX_X - trap_length / 2,
        y=MIN_Y + bar_thickness / 2,
        length=trap_length,
        angle=-10.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    ground_length = right_trap.left - left_trap.right
    ground_x = (right_trap.left + left_trap.right) / 2
    purple_ground = Bar.from_point_and_angle(
        x=ground_x,
        y=MIN_Y + bar_thickness / 2,
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
        name="task00108",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball to the purple ground."},
    )
