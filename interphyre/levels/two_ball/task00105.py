import numpy as np
from typing import cast
from interphyre.objects import Ball, Basket, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.levels.two_ball._constants import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


def _basket_with_ball(rng, platform, right: bool):
    obstacle_length = 0.02 * WORLD_WIDTH
    bar_thickness = platform.thickness

    if right:
        obstacle_x = platform.right - bar_thickness / 2
    else:
        obstacle_x = platform.left + bar_thickness / 2
    obstacle = Bar(
        top=platform.top + obstacle_length,
        bottom=platform.top,
        x=obstacle_x,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    basket_scale = 0.2 * WORLD_WIDTH / 2
    basket_angle = 146.0 if right else -146.0
    offset = platform.length / 2 + (0.04 * WORLD_WIDTH if right else -0.04 * WORLD_HEIGHT)
    basket_x = platform.left + offset
    basket_y = platform.top
    basket = Basket(
        x=basket_x,
        y=basket_y,
        scale=basket_scale,
        angle=basket_angle,
        anchor="bottom_center",
        color="gray",
        dynamic=True,
    )

    ball_radius = 0.1 * WORLD_WIDTH / 2
    basket_left = basket_x - basket.bottom_width / 2
    basket_right = basket_x + basket.bottom_width / 2
    ball_offset = (basket_right - basket_left) * 0.7
    ball_x = basket_right - ball_offset if right else basket_left + ball_offset
    ball_y = basket_y + ball_radius
    ball = Ball(
        x=ball_x,
        y=ball_y,
        radius=ball_radius,
        color="blue" if right else "green",
        dynamic=True,
    )
    return basket, ball, obstacle


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    platform_x_options = [val * 0.05 for val in range(6, 16)]
    platform_y_options = [val * 0.1 for val in range(0, 8)]

    while True:
        platform1_x = rng.choice(platform_x_options)
        platform2_x = rng.choice(platform_x_options)
        platform1_y = rng.choice(platform_y_options)
        platform2_y = rng.choice(platform_y_options)
        if platform1_x + 0.3 >= platform2_x:
            continue
        if abs(platform1_y - platform2_y) >= 0.3:
            continue
        break

    bar_thickness = 0.2
    platform_length = 0.2 * WORLD_WIDTH
    platform1 = Bar.from_point_and_angle(
        x=MIN_X + platform1_x * WORLD_WIDTH,
        y=MIN_Y + platform1_y * WORLD_HEIGHT + bar_thickness / 2,
        length=platform_length,
        angle=0.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    platform2 = Bar.from_point_and_angle(
        x=MIN_X + platform2_x * WORLD_WIDTH,
        y=MIN_Y + platform2_y * WORLD_HEIGHT + bar_thickness / 2,
        length=platform_length,
        angle=0.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    basket1, green_ball, obstacle1 = _basket_with_ball(rng, platform1, right=False)
    basket2, blue_ball, obstacle2 = _basket_with_ball(rng, platform2, right=True)

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
        "basket_1": basket1,
        "basket_2": basket2,
        "platform_1": platform1,
        "platform_2": platform2,
        "obstacle_1": obstacle1,
        "obstacle_2": obstacle2,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00105",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
