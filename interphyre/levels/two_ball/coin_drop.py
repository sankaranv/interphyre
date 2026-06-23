import numpy as np
from interphyre.objects import Ball, Basket, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_basket", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    ball_sizes = [0.075, 0.1, 0.125]
    hole_sizes = [0.15, 0.2, 0.25]
    basket_sizes = [0.2, 0.25]
    hole_lefts = [0.3, 0.4, 0.5, 0.6]
    bar_heights = [0.4, 0.5]
    bar_thickness = 0.2

    hole_left_frac = rng.choice(hole_lefts)
    hole_size_frac = rng.choice(hole_sizes)
    hole_right_frac = hole_left_frac + hole_size_frac
    left_wall = rng.choice([True, False])
    bar_height = rng.choice(bar_heights)

    bar_y = MIN_Y + bar_height * WORLD_HEIGHT + bar_thickness / 2
    hole_left_x = MIN_X + hole_left_frac * WORLD_WIDTH
    hole_right_x = MIN_X + hole_right_frac * WORLD_WIDTH

    left_bar = Bar(
        left=MIN_X,
        right=hole_left_x,
        y=bar_y,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_bar = Bar(
        left=hole_right_x,
        right=MAX_X,
        y=bar_y,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    ball_size = rng.choice(ball_sizes)
    ball_radius = ball_size * WORLD_WIDTH / 2
    green_ball_frac = hole_left_frac if left_wall else hole_right_frac
    green_ball_x = MIN_X + green_ball_frac * WORLD_WIDTH
    green_ball_y = MIN_Y + 0.6 * WORLD_HEIGHT + ball_radius
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    basket_scale = rng.choice(basket_sizes) * WORLD_WIDTH / 2
    blue_basket = Basket(
        x=green_ball_x,
        y=MIN_Y + 0.1,
        scale=basket_scale,
        anchor="bottom_center",
        color="blue",
        dynamic=True,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "green_ball": green_ball,
        "blue_basket": blue_basket,
        "left_bar": left_bar,
        "right_bar": right_bar,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="coin_drop",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Drop the green ball into the blue basket."},
    )
