import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT
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
    ball_radius = 0.07 * WORLD_WIDTH / 2
    ball_top = MIN_X + 0.93 * WORLD_WIDTH
    green_ball_x = MIN_X + rng.uniform(0.2, 0.8) * WORLD_WIDTH
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
    cap_length = 0.08 * WORLD_WIDTH
    bar_lengths = [1.4, 1.9, 2.4, 2.9]
    center_x_options = [-3.2, -1.8, -0.4, 0.8, 2.2, 3.2]
    y_positions = np.linspace(
        0.15,
        (ball_top - 2 * ball_radius - MIN_X) / WORLD_WIDTH,
        bar_count,
    )
    for idx, y_frac in enumerate(reversed(y_positions)):
        bar_length = rng.choice(bar_lengths)
        center_x = green_ball_x if idx == 0 else rng.choice(center_x_options)
        bar_y = MIN_X + (y_frac + rng.normal() * 0.015) * WORLD_WIDTH
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

    lower_bar_length = 2.0 * WORLD_WIDTH / 5
    lower_bar = Bar(
        left=MIN_X + 0.35 * WORLD_WIDTH,
        right=MIN_X + 0.35 * WORLD_WIDTH + lower_bar_length,
        y=MIN_X + 0.12 * WORLD_WIDTH + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    objects["lower_bar"] = lower_bar

    pair_length = 0.2 * WORLD_WIDTH
    pair_y = MIN_X + 0.25 * WORLD_WIDTH
    pair_top = Bar(
        left=MAX_X - 0.35 * WORLD_WIDTH,
        right=MAX_X - 0.35 * WORLD_WIDTH + pair_length,
        y=pair_y + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    pair_bottom = Bar(
        left=pair_top.left + 0.03 * WORLD_WIDTH,
        right=pair_top.right - 0.03 * WORLD_WIDTH,
        y=pair_y - 0.07 * WORLD_WIDTH + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    objects["pair_top"] = pair_top
    objects["pair_bottom"] = pair_bottom

    trap_length = 0.15 * WORLD_WIDTH
    left_trap = Bar.from_point_and_angle(
        x=MIN_X + trap_length / 2,
        y=MIN_X + bar_thickness / 2,
        angle=10.0,
        length=trap_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_trap = Bar.from_point_and_angle(
        x=MAX_X - trap_length / 2,
        y=MIN_X + bar_thickness / 2,
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
        y=MIN_X + bar_thickness / 2,
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
