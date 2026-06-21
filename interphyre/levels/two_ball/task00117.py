import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.levels.two_ball._constants import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "target", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    fulcrum_x_options = np.linspace(0.2, 0.4, 10)
    beam_angle_options = np.linspace(15, 30, 10)
    beam_size_options = np.linspace(0.35, 0.5, 10)

    bar_thickness = 0.2
    fulcrum_x = rng.choice(fulcrum_x_options)
    beam_angle = rng.choice(beam_angle_options)
    beam_size = rng.choice(beam_size_options)

    target_y = 0.6
    target_height = (1.0 - target_y) * WORLD_HEIGHT
    target_bottom = MIN_Y + target_y * WORLD_HEIGHT
    target = Bar(
        top=target_bottom + target_height,
        bottom=target_bottom,
        x=MAX_X - bar_thickness / 2,
        thickness=bar_thickness,
        color="purple",
        dynamic=False,
    )
    target_ramp = Bar.from_point_and_angle(
        x=MAX_X - 0.12 * WORLD_WIDTH,
        y=MIN_Y + target_y * WORLD_HEIGHT + bar_thickness / 2,
        angle=-10.0,
        length=0.25 * WORLD_WIDTH,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    fulcrum_radius = 0.10 * WORLD_WIDTH / 2
    fulcrum = Ball(
        x=MIN_X + fulcrum_x * WORLD_WIDTH,
        y=MIN_Y + fulcrum_radius,
        radius=fulcrum_radius,
        color="black",
        dynamic=False,
    )

    beam_length = beam_size * WORLD_WIDTH
    offset = 0.5 * beam_size * np.sin(np.radians(beam_angle)) * WORLD_HEIGHT
    beam_bottom = fulcrum.y + fulcrum.radius - offset
    beam = Bar.from_point_and_angle(
        x=fulcrum.x,
        y=beam_bottom + bar_thickness / 2,
        angle=beam_angle,
        length=beam_length,
        thickness=bar_thickness,
        color="black",
        dynamic=True,
    )

    ball_radius = 0.1 * WORLD_WIDTH / 2
    ball_x = (fulcrum_x + 0.5 * beam_size * np.cos(np.radians(beam_angle))) * WORLD_WIDTH + MIN_X
    green_ball = Ball(
        x=ball_x,
        y=beam.top + ball_radius,
        radius=ball_radius,
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
        "green_ball": green_ball,
        "fulcrum": fulcrum,
        "beam": beam,
        "target": target,
        "target_ramp": target_ramp,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00117",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball to touch the target bar."},
    )
