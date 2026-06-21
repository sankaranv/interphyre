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

    step_diff = rng.choice(np.linspace(-0.3, 0.3, 10))
    step_base = rng.choice(np.linspace(0.01, 0.1, 2))
    basket_scale = rng.choice(np.linspace(0.15, 0.3, 3))
    basket_right = rng.choice(np.linspace(0.9, 0.98, 3))
    basket_angle = rng.choice(np.linspace(-10, 10, 13))

    if step_diff > 0:
        left_step_height = step_base
        right_step_height = left_step_height + step_diff
    else:
        right_step_height = step_base
        left_step_height = right_step_height - step_diff

    if basket_scale < 0.19 and abs(step_diff) > 0.19:
        step_diff = 0.1 * np.sign(step_diff)
    if basket_scale > 0.26 and abs(step_diff) < 0.19:
        step_diff = 0.2
    if basket_scale > 0.26 and step_diff < -0.19:
        step_diff = -0.15

    bar_thickness = 0.2
    left_step = Bar(
        left=(-5.0) + 0.1 * (10.0),
        right=(-5.0) + 0.4 * (10.0),
        y=(-5.0) + left_step_height * (10.0) + bar_thickness / 2,
        thickness=bar_thickness,
        color="gray",
        dynamic=False,
    )

    beam = Bar(
        left=(-5.0) + 0.05 * (10.0),
        right=(-5.0) + 0.45 * (10.0),
        y=left_step.top + bar_thickness / 2 + 0.5,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )

    ball_radius = 0.05 * (10.0) / 2
    green_ball = Ball(
        x=(-5.0) + 0.02 * (10.0) + ball_radius,
        y=beam.top + ball_radius,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    right_step = Bar.from_point_and_angle(
        x=(5.0) - 0.15 * (10.0),
        y=(-5.0) + right_step_height * (10.0) + bar_thickness / 2,
        length=0.3 * (10.0),
        angle=basket_angle,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    basket_scale_world = basket_scale * (10.0) / 2
    basket_x = (-5.0) + basket_right * (10.0)
    basket_y = right_step.top
    basket = Basket(
        x=basket_x,
        y=basket_y,
        scale=basket_scale_world,
        anchor="bottom_center",
        color="gray",
        dynamic=True,
    )
    ball_in_basket_radius = (0.05 + basket_scale / 8) * (10.0) / 2
    blue_ball = Ball(
        x=basket.x,
        y=basket.y + ball_in_basket_radius,
        radius=ball_in_basket_radius,
        color="blue",
        dynamic=True,
    )

    lower_bar = Bar(
        left=(-5.0) + 0.15 * (10.0),
        right=(-5.0) + 0.45 * (10.0),
        y=(-5.0) + 0.15 * (10.0) + bar_thickness / 2,
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
        "left_step": left_step,
        "right_step": right_step,
        "beam": beam,
        "basket": basket,
        "lower_bar": lower_bar,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00119",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
