import numpy as np
from interphyre.objects import Ball, Basket, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    center_y_options = np.linspace(0.2, 0.7, 5)
    jar_sizes = [0.3, 0.35]

    bar_thickness = 0.2
    ball_radius = 0.07 * WORLD_WIDTH / 2

    y1 = rng.choice(center_y_options)
    y2 = rng.choice(center_y_options)

    # Constraints: not (j1_left and j1_size==0.35) and not (not j2_left and j2_size==0.35).
    j1_size = rng.choice(jar_sizes)
    j1_left = rng.choice([True, False]) if j1_size != 0.35 else False
    j2_size = rng.choice(jar_sizes)
    j2_left = rng.choice([True, False]) if j2_size != 0.35 else True

    # V-shaped ground slopes meeting at scene center bottom.
    slope_length = WORLD_WIDTH
    half_span = slope_length / 2 * np.cos(np.radians(15.0))
    slope_rise = slope_length / 2 * np.sin(np.radians(15.0))
    left_slope = Bar.from_point_and_angle(
        x=half_span,
        y=MIN_Y + slope_rise,
        angle=15.0,
        length=slope_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_slope = Bar.from_point_and_angle(
        x=-half_span,
        y=MIN_Y + slope_rise,
        angle=-15.0,
        length=slope_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Two tilted jars (~85°), static, at 25% and 75% of scene width.
    jar1_scale = j1_size * WORLD_WIDTH / 2
    jar1_x = MIN_X + 0.25 * WORLD_WIDTH
    jar1_y = MIN_Y + y1 * WORLD_WIDTH
    jar1 = Basket(
        x=jar1_x,
        y=jar1_y,
        scale=jar1_scale,
        angle=85.0 if j1_left else -85.0,
        anchor="bottom_center",
        color="gray",
        dynamic=False,
    )
    # Ball beside jar1 opening, offset by 0.03*W from the jar's edge.
    jar1_half_width = jar1.total_width / 2
    if j1_left:
        ball1_x = jar1_x - jar1_half_width - 0.03 * WORLD_WIDTH + ball_radius
    else:
        ball1_x = jar1_x + jar1_half_width + 0.03 * WORLD_WIDTH - ball_radius
    green_ball = Ball(
        x=ball1_x,
        y=jar1_y + 0.02 * WORLD_WIDTH + ball_radius,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    jar2_scale = j2_size * WORLD_WIDTH / 2
    jar2_x = MIN_X + 0.75 * WORLD_WIDTH
    jar2_y = MIN_Y + y2 * WORLD_WIDTH
    jar2 = Basket(
        x=jar2_x,
        y=jar2_y,
        scale=jar2_scale,
        angle=85.0 if j2_left else -85.0,
        anchor="bottom_center",
        color="gray",
        dynamic=False,
    )
    jar2_half_width = jar2.total_width / 2
    if j2_left:
        ball2_x = jar2_x - jar2_half_width - 0.03 * WORLD_WIDTH + ball_radius
    else:
        ball2_x = jar2_x + jar2_half_width + 0.03 * WORLD_WIDTH - ball_radius
    blue_ball = Ball(
        x=ball2_x,
        y=jar2_y + 0.02 * WORLD_WIDTH + ball_radius,
        radius=ball_radius,
        color="blue",
        dynamic=True,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "green_ball": green_ball,
        "blue_ball": blue_ball,
        "jar_1": jar1,
        "jar_2": jar2,
        "left_slope": left_slope,
        "right_slope": right_slope,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00118",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
