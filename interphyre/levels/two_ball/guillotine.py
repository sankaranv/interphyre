import numpy as np
from interphyre.objects import Ball, Basket, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    bar_y_options = np.linspace(0.4, 0.7, 10)
    bottom_basket_scales = np.linspace(0.15, 0.20, 3)
    bottom_basket_xs = np.linspace(0.25, 0.50, 5)
    left_diag_angles = np.linspace(30, 70, 3)
    right_diag_angles = np.linspace(30, 70, 3)

    bar_thickness = 0.2
    bar_y = rng.choice(bar_y_options)
    bottom_basket_scale = rng.choice(bottom_basket_scales)
    bottom_basket_x = rng.choice(bottom_basket_xs)
    left_diag_angle = rng.choice(left_diag_angles)
    right_diag_angle = rng.choice(right_diag_angles)

    basket_scale = bottom_basket_scale * WORLD_WIDTH / 2
    basket_x = MIN_X + bottom_basket_x * WORLD_WIDTH
    bottom_basket = Basket(
        x=basket_x,
        y=MIN_Y,
        scale=basket_scale,
        anchor="bottom_center",
        color="gray",
        dynamic=True,
    )

    ball_in_basket_radius = (0.03 + bottom_basket_scale / 5) * WORLD_WIDTH / 2
    blue_ball = Ball(
        x=basket_x,
        y=MIN_Y + ball_in_basket_radius,
        radius=ball_in_basket_radius,
        color="blue",
        dynamic=True,
    )

    # Bar extends from basket's left edge to right edge of scene.
    basket_left = basket_x - bottom_basket.bottom_width / 2
    bar_length = (0.8 - (basket_left - MIN_X) / WORLD_WIDTH) * WORLD_WIDTH
    bar = Bar(
        left=basket_left,
        right=basket_left + bar_length,
        y=MIN_Y + bar_y * WORLD_HEIGHT + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Upside-down cover sits above the bar, with its anchor point ~2.5 units above the bar top.
    cover_scale = 0.1 * WORLD_WIDTH / 2
    cover = Basket(
        x=bar.left + cover_scale * 0.6,
        y=bar.top + 2.3,
        scale=cover_scale,
        angle=180.0,
        anchor="bottom_center",
        color="gray",
        dynamic=True,
    )

    green_ball_radius = 0.05 * WORLD_WIDTH / 2
    green_ball = Ball(
        x=cover.x,
        y=bar.top + green_ball_radius,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    # Small upright at bar's right edge.
    right_upright_length = 0.15 * WORLD_WIDTH
    right_upright = Bar(
        top=bar.top + right_upright_length,
        bottom=bar.top,
        x=bar.right - bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    left_diag = Bar.from_point_and_angle(
        x=MAX_X - 0.1 * WORLD_WIDTH,
        y=MIN_Y + bar_thickness / 2,
        angle=left_diag_angle,
        length=WORLD_WIDTH,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_diag = Bar.from_point_and_angle(
        x=MIN_X + 0.1 * WORLD_WIDTH,
        y=MIN_Y + bar_thickness / 2,
        angle=-right_diag_angle,
        length=WORLD_WIDTH,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "green_ball": green_ball,
        "blue_ball": blue_ball,
        "bottom_basket": bottom_basket,
        "cover_basket": cover,
        "bar": bar,
        "right_upright": right_upright,
        "left_diag": left_diag,
        "right_diag": right_diag,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="guillotine",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
