import numpy as np

from interphyre.config import MAX_X, MIN_X, MIN_Y, WORLD_HEIGHT, WORLD_WIDTH
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Bar, Basket


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    step_diffs = np.linspace(-0.3, 0.3, 10)
    step_bases = np.linspace(0.01, 0.1, 2)
    jar_scales = np.linspace(0.15, 0.3, 3)  # [0.15, 0.225, 0.3]
    jar_rights = np.linspace(0.9, 0.98, 3)
    jar_angles = np.linspace(-10, 10, 13)

    bar_thickness = 0.2

    # Constrain step_diff based on jar_scale: larger jars require larger steps to ensure clearance.
    jar_scale = rng.choice(jar_scales)
    if jar_scale < 0.19:
        valid_step_diffs = [d for d in step_diffs if abs(d) <= 0.19]
    elif jar_scale > 0.26:
        valid_step_diffs = [d for d in step_diffs if abs(d) >= 0.19 and d >= -0.19]
    else:
        valid_step_diffs = list(step_diffs)
    step_diff = rng.choice(valid_step_diffs)
    step_base = rng.choice(step_bases)
    jar_right = rng.choice(jar_rights)
    jar_angle = rng.choice(jar_angles)

    if step_diff > 0:
        left_step_height = step_base
        right_step_height = left_step_height + step_diff
    else:
        right_step_height = step_base
        left_step_height = right_step_height - step_diff

    left_step = Bar(
        left=MIN_X + 0.1 * WORLD_WIDTH,
        right=MIN_X + 0.4 * WORLD_WIDTH,
        y=MIN_Y + left_step_height * WORLD_HEIGHT + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Dynamic beam floating 50px above the left step.
    beam = Bar(
        left=MIN_X + 0.05 * WORLD_WIDTH,
        right=MIN_X + 0.45 * WORLD_WIDTH,
        y=left_step.top + 0.5 + bar_thickness / 2,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )

    ball_radius = 0.05 * WORLD_WIDTH / 2
    green_ball = Ball(
        x=MIN_X + 0.02 * WORLD_WIDTH + ball_radius,
        y=beam.top + ball_radius,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    right_step = Bar.from_point_and_angle(
        x=MAX_X - 0.15 * WORLD_WIDTH,
        y=MIN_Y + right_step_height * WORLD_HEIGHT + bar_thickness / 2,
        length=0.3 * WORLD_WIDTH,
        angle=jar_angle,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    basket_scale_world = jar_scale * WORLD_WIDTH / 2
    basket_x = MIN_X + jar_right * WORLD_WIDTH
    basket = Basket(
        x=basket_x,
        y=right_step.top,
        scale=basket_scale_world,
        anchor="bottom_center",
        color="gray",
        dynamic=True,
    )

    ball_in_jar_radius = (0.05 + jar_scale / 8) * WORLD_WIDTH / 2
    blue_ball = Ball(
        x=basket.x,
        y=basket.y + ball_in_jar_radius,
        radius=ball_in_jar_radius,
        color="blue",
        dynamic=True,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "green_ball": green_ball,
        "blue_ball": blue_ball,
        "left_step": left_step,
        "right_step": right_step,
        "beam": beam,
        "basket": basket,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="missing_piece",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
