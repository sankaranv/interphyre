import numpy as np

from interphyre.config import MAX_X, MIN_X, MIN_Y, WORLD_HEIGHT, WORLD_WIDTH
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Bar


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "target_ramp", success_time
    ) or engine.is_in_contact_for_duration("green_ball", "target", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    fulcrum_x_options = np.linspace(0.2, 0.4, 10)
    beam_angle_options = np.linspace(15, 30, 10)
    beam_size_options = np.linspace(0.35, 0.5, 10)

    bar_thickness = 0.2
    fulcrum_scale = 0.10
    fulcrum_radius = fulcrum_scale * WORLD_WIDTH / 2

    # Constraint: beam.left >= MIN_X → fulcrum_x >= beam_size/2*cos(angle).
    # Constraint: beam.bottom >= MIN_Y → beam_size * sin(angle) <= 2*fulcrum_radius/W = 0.1.
    fulcrum_x = rng.choice(fulcrum_x_options)
    valid_combos = [
        (bs, ba)
        for bs in beam_size_options
        for ba in beam_angle_options
        if fulcrum_x >= bs / 2 * np.cos(np.radians(ba)) + 0.01
        and bs * np.sin(np.radians(ba)) <= 0.1
    ]
    if not valid_combos:
        valid_combos = [(beam_size_options[0], beam_angle_options[0])]
    combo_idx = rng.integers(len(valid_combos))
    beam_size, beam_angle = valid_combos[combo_idx]

    target_y = 0.6
    target_height = (1.0 - target_y) * WORLD_HEIGHT
    target = Bar(
        top=MIN_Y + target_y * WORLD_HEIGHT + target_height,
        bottom=MIN_Y + target_y * WORLD_HEIGHT,
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
        color="purple",
        dynamic=False,
    )

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
        color="gray",
        dynamic=True,
    )

    ball_radius = 0.1 * WORLD_WIDTH / 2
    ball_x = (
        MIN_X
        + (fulcrum_x + 0.5 * beam_size * np.cos(np.radians(beam_angle))) * WORLD_WIDTH
    )
    green_ball = Ball(
        x=ball_x,
        y=beam.top + ball_radius,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

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
        name="trebuchet",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball to touch the target bar."},
    )
