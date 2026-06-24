import numpy as np
from interphyre.objects import Ball, Basket
from interphyre.level import Level
from interphyre.config import MIN_X, MIN_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    ball_size = 0.1
    x_options = np.linspace(0.1, 0.9, 8)
    y_options = np.linspace(0.5, 0.8, 8)

    # Blue ball must be at least 0.2 fraction to the right of green ball.
    valid_ball1_x = x_options[x_options + 0.2 < x_options[-1]]
    ball1_x = rng.choice(valid_ball1_x)
    valid_ball2_x = x_options[x_options > ball1_x + 0.2]
    ball2_x = rng.choice(valid_ball2_x)

    ball1_y = rng.choice(y_options)
    ball2_y = rng.choice(y_options)

    ball_radius = ball_size * WORLD_WIDTH / 2
    green_ball_x = MIN_X + ball1_x * WORLD_WIDTH
    blue_ball_x = MIN_X + ball2_x * WORLD_WIDTH
    green_ball_y = MIN_Y + ball1_y * WORLD_HEIGHT + ball_radius
    blue_ball_y = MIN_Y + ball2_y * WORLD_HEIGHT + ball_radius

    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )
    blue_ball = Ball(
        x=blue_ball_x,
        y=blue_ball_y,
        radius=ball_radius,
        color="blue",
        dynamic=True,
    )

    basket_scale = 0.15 * WORLD_WIDTH / 2
    green_basket = Basket(
        x=green_ball_x,
        y=MIN_Y + 0.1,
        scale=basket_scale,
        anchor="bottom_center",
        color="gray",
        dynamic=True,
    )
    blue_basket = Basket(
        x=blue_ball_x,
        y=MIN_Y + 0.1,
        scale=basket_scale,
        anchor="bottom_center",
        color="gray",
        dynamic=True,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "green_ball": green_ball,
        "blue_ball": blue_ball,
        "green_basket": green_basket,
        "blue_basket": blue_basket,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="no_mans_land",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
