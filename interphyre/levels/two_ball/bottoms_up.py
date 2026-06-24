import numpy as np
from interphyre.objects import Ball, Basket, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MIN_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


def _ball_in_basket(jar_x, jar_y, angle_deg, bottom_width, floor_thickness, ball_radius, opening_left):
    """World-space position for a ball resting inside a near-horizontal basket.

    At angle ≈ ±85° the basket lies on its side. Gravity's component in the basket's
    local frame presses the ball against the side-wall that now faces downward in world
    space: the local right wall when opening_left=False (angle=-85°), the local left
    wall when opening_left=True (angle=+85°).
    """
    angle_rad = np.radians(angle_deg)
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)

    x_local = -(bottom_width / 2 - ball_radius) if opening_left else (bottom_width / 2 - ball_radius)
    y_local = floor_thickness + ball_radius  # just inside the basket floor

    # Rotate local position into world space (R(angle) * local + anchor).
    ball_x = jar_x + cos_a * x_local - sin_a * y_local
    ball_y = jar_y + sin_a * x_local + cos_a * y_local
    return float(ball_x), float(ball_y)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    # Jar sizes are constrained so the two baskets never intersect each other.
    # At angle=±85° each basket's opening extends ≈ total_height × sin(85°) toward
    # the center. With baskets placed at x=±2.5, scale≤1.0 gives max extent ≈2.17,
    # leaving a clear margin before the opposite basket (center gap = 5.0).
    jar_sizes = [0.18, 0.2]
    center_y_options = np.linspace(0.2, 0.7, 5)

    bar_thickness = 0.2
    ball_radius = 0.07 * WORLD_WIDTH / 2

    y1 = rng.choice(center_y_options)
    y2 = rng.choice(center_y_options)
    j1_size = rng.choice(jar_sizes)
    j1_left = rng.choice([True, False])
    j2_size = rng.choice(jar_sizes)
    j2_left = rng.choice([True, False])

    # V-shaped ground slopes meeting at scene center bottom.
    slope_length = WORLD_WIDTH
    half_span = slope_length / 2 * np.cos(np.radians(15.0))
    slope_rise = slope_length / 2 * np.sin(np.radians(15.0))
    left_slope = Bar.from_point_and_angle(
        x=-half_span,
        y=MIN_Y + slope_rise,
        angle=-15.0,
        length=slope_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_slope = Bar.from_point_and_angle(
        x=half_span,
        y=MIN_Y + slope_rise,
        angle=15.0,
        length=slope_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Two baskets tilted ~85° from upright, fixed at 25% and 75% of scene width.
    # The opening faces sideways toward the center; balls rest inside against the
    # wall that gravity presses them onto.
    jar1_scale = j1_size * WORLD_WIDTH / 2
    jar1_x = MIN_X + 0.25 * WORLD_WIDTH
    jar1_y = MIN_Y + y1 * WORLD_HEIGHT
    jar1_angle = 85.0 if j1_left else -85.0
    jar1 = Basket(
        x=jar1_x,
        y=jar1_y,
        scale=jar1_scale,
        angle=jar1_angle,
        anchor="bottom_center",
        color="gray",
        dynamic=False,
    )
    green_ball_x, green_ball_y = _ball_in_basket(
        jar1_x, jar1_y, jar1_angle,
        jar1.bottom_width, jar1.floor_thickness, ball_radius, j1_left,
    )
    green_ball = Ball(x=green_ball_x, y=green_ball_y, radius=ball_radius, color="green", dynamic=True)

    jar2_scale = j2_size * WORLD_WIDTH / 2
    jar2_x = MIN_X + 0.75 * WORLD_WIDTH
    jar2_y = MIN_Y + y2 * WORLD_HEIGHT
    jar2_angle = 85.0 if j2_left else -85.0
    jar2 = Basket(
        x=jar2_x,
        y=jar2_y,
        scale=jar2_scale,
        angle=jar2_angle,
        anchor="bottom_center",
        color="gray",
        dynamic=False,
    )
    blue_ball_x, blue_ball_y = _ball_in_basket(
        jar2_x, jar2_y, jar2_angle,
        jar2.bottom_width, jar2.floor_thickness, ball_radius, j2_left,
    )
    blue_ball = Ball(x=blue_ball_x, y=blue_ball_y, radius=ball_radius, color="blue", dynamic=True)

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
        name="bottoms_up",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
