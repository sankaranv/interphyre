import numpy as np
from typing import cast
from interphyre.objects import Ball, Basket, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

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

    basket_scale = bottom_basket_scale * (10.0) / 2
    basket_x = (-5.0) + bottom_basket_x * (10.0)
    basket_y = (-5.0) + 0.1
    bottom_basket = Basket(
        x=basket_x,
        y=basket_y,
        scale=basket_scale,
        anchor="bottom_center",
        color="gray",
        dynamic=True,
    )
    basket_left = bottom_basket.x - bottom_basket.bottom_width / 2

    ball_in_basket_radius = (0.03 + bottom_basket_scale / 5) * (10.0) / 2
    blue_ball = Ball(
        x=basket_x,
        y=basket_y + ball_in_basket_radius,
        radius=ball_in_basket_radius,
        color="blue",
        dynamic=True,
    )

    bar_bottom = (-5.0) + bar_y * (10.0)
    bar_length = (0.8 - (basket_left - (-5.0)) / (10.0)) * (10.0)
    bar = Bar(
        left=basket_left,
        right=basket_left + bar_length,
        y=bar_bottom + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    cover_scale = 0.1 * (10.0) / 2
    cover_x = bar.left + cover_scale
    cover_y = bar.top + 0.2
    cover = Basket(
        x=cover_x,
        y=cover_y,
        scale=cover_scale,
        angle=180.0,
        anchor="bottom_center",
        color="gray",
        dynamic=True,
    )

    cover_ball_radius = 0.05 * (10.0) / 2
    cover_left = cover.x - cover.bottom_width / 2
    green_ball_x = cover_left + cover.bottom_width * 0.5
    green_ball = Ball(
        x=green_ball_x,
        y=bar.top + cover_ball_radius,
        radius=cover_ball_radius,
        color="green",
        dynamic=True,
    )

    right_upright_length = 0.15 * (10.0)
    right_upright = Bar(
        top=bar.top + right_upright_length,
        bottom=bar.top,
        x=bar.right,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    left_diag = Bar.from_point_and_angle(
        x=(5.0) - 0.1 * (10.0),
        y=(-5.0) + bar_thickness / 2,
        angle=left_diag_angle,
        length=(10.0),
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_diag = Bar.from_point_and_angle(
        x=(-5.0) + 0.1 * (10.0),
        y=(-5.0) + bar_thickness / 2,
        angle=-right_diag_angle,
        length=(10.0),
        thickness=bar_thickness,
        color="black",
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
        name="task00113",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
