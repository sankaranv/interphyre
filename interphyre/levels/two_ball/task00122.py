import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("falling_sticks", "purple_ground", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    scale_options = np.linspace(0.5, 0.7, 4)
    scale2_options = np.linspace(0.4, 0.6, 4)
    center_x_options = np.linspace(0.4, 0.7, 5)
    height_options = np.linspace(0.0, 0.075, 2)
    left_options = [True, False]

    scale = rng.choice(scale_options)
    scale2 = rng.choice(scale2_options)
    center_x = rng.choice(center_x_options)
    height = rng.choice(height_options)
    left = rng.choice(left_options)

    bar_thickness = 0.2
    ground = Bar(
        left=MIN_X,
        right=MAX_X,
        y=MIN_X + height * WORLD_WIDTH + bar_thickness / 2,
        thickness=bar_thickness,
        color="purple",
        dynamic=False,
    )

    base_length = scale * WORLD_WIDTH
    base_bottom = ground.top
    base_top = base_bottom + base_length
    base_x = MIN_X + center_x * WORLD_WIDTH
    base = Bar(
        top=base_top,
        bottom=base_bottom,
        x=base_x,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    falling_length = scale2 * WORLD_WIDTH
    falling_x = (
        base.left + 0.1 * scale2 * WORLD_WIDTH
        if left
        else base.right - 0.1 * scale2 * WORLD_WIDTH
    )
    falling_y = base.top - 0.10 * scale2 * WORLD_WIDTH + falling_length / 2
    falling_sticks = Bar.from_point_and_angle(
        x=falling_x,
        y=falling_y,
        angle=35.0 if left else -35.0,
        length=falling_length,
        thickness=bar_thickness,
        color="green",
        dynamic=True,
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
        "base": base,
        "falling_sticks": falling_sticks,
        "purple_ground": ground,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00122",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the falling sticks touch the ground."},
    )
