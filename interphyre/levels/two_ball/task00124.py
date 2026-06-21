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

    base_y_options = np.linspace(0.02, 0.12, 6)
    base_x_options = np.linspace(0.4, 0.6, 5)
    scale_options = [0.5, 0.6, 0.7]

    base_y = rng.choice(base_y_options)
    base_x = rng.choice(base_x_options)
    scale = rng.choice(scale_options)

    bar_thickness = 0.2
    base_length = 0.2 * WORLD_WIDTH
    base_x_world = MIN_X + base_x * WORLD_WIDTH
    base_bottom = MIN_Y + base_y * WORLD_HEIGHT
    base = Bar(
        left=base_x_world - base_length / 2,
        right=base_x_world + base_length / 2,
        y=base_bottom + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    sticks_length = scale * WORLD_HEIGHT
    sticks_bottom = base.top
    sticks_top = sticks_bottom + sticks_length
    left_stick = Bar.from_point_and_angle(
        x=base.x - 0.05 * WORLD_WIDTH,
        y=(sticks_bottom + sticks_top) / 2,
        angle=25.0,
        length=sticks_length,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )
    right_stick = Bar.from_point_and_angle(
        x=base.x + 0.05 * WORLD_WIDTH,
        y=(sticks_bottom + sticks_top) / 2,
        angle=-25.0,
        length=sticks_length,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )

    ball_radius = 0.03 * WORLD_WIDTH / 2
    green_ball = Ball(
        x=base.x,
        y=sticks_top - ball_radius - 0.03 * WORLD_HEIGHT,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    top_bar = Bar(
        left=base.x - 0.075 * WORLD_WIDTH,
        right=base.x + 0.075 * WORLD_WIDTH,
        y=sticks_top + 0.05 * WORLD_HEIGHT + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    left_ball = Ball(
        x=base.x - 0.1 * WORLD_WIDTH,
        y=sticks_bottom + (sticks_length / 2),
        radius=ball_radius,
        color="gray",
        dynamic=True,
    )
    right_ball = Ball(
        x=base.x + 0.1 * WORLD_WIDTH,
        y=sticks_bottom + (sticks_length / 2),
        radius=ball_radius,
        color="gray",
        dynamic=True,
    )

    purple_ground = Bar(
        left=MIN_X,
        right=MAX_X,
        y=MIN_Y + bar_thickness / 2,
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
        "base": base,
        "left_stick": left_stick,
        "right_stick": right_stick,
        "top_bar": top_bar,
        "left_ball": left_ball,
        "right_ball": right_ball,
        "purple_ground": purple_ground,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00124",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball to the purple ground."},
    )
