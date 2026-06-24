import numpy as np
from interphyre.objects import Ball, Basket, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MIN_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


def _jar_with_ball(platform: Bar, right: bool, ball_color: str) -> tuple:
    bar_thickness = platform.thickness
    obstacle_height = 0.02 * WORLD_WIDTH

    # Obstacle at platform edge facing away from jar opening.
    if right:
        obstacle_x = platform.right - bar_thickness / 2
    else:
        obstacle_x = platform.left + bar_thickness / 2
    obstacle = Bar(
        top=platform.top + obstacle_height,
        bottom=platform.top,
        x=obstacle_x,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Upside-down jar offset from platform center: 0.04*W toward the inner side.
    basket_scale = 0.2 * WORLD_WIDTH / 2
    inner_offset = 0.04 * WORLD_WIDTH
    basket_x = platform.x + (inner_offset if right else -inner_offset)
    basket = Basket(
        x=basket_x,
        y=platform.top,
        scale=basket_scale,
        angle=146.0 if right else -146.0,
        anchor="bottom_center",
        color="gray",
        dynamic=True,
    )

    # Ball inside the jar, positioned at 30% from the outer edge of the jar.
    ball_radius = 0.1 * WORLD_WIDTH / 2
    ball_offset = basket_scale * 0.6
    ball_x = basket_x + (-ball_offset if right else ball_offset)
    ball = Ball(
        x=ball_x,
        y=platform.top + ball_radius,
        radius=ball_radius,
        color=ball_color,
        dynamic=True,
    )
    return basket, ball, obstacle


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    platform_x_options = [val * 0.05 for val in range(6, 16)]
    platform_y_options = [val * 0.1 for val in range(0, 8)]
    bar_thickness = 0.2
    platform_length = 0.2 * WORLD_WIDTH

    # Second platform must be at least 0.3 to the right of the first.
    valid_p1_x = [x for x in platform_x_options if x + 0.3 < platform_x_options[-1]]
    platform1_x = rng.choice(valid_p1_x)
    valid_p2_x = [x for x in platform_x_options if x > platform1_x + 0.3]
    platform2_x = rng.choice(valid_p2_x)

    # Heights must not differ by 0.3 or more.
    platform1_y = rng.choice(platform_y_options)
    valid_p2_y = [y for y in platform_y_options if abs(y - platform1_y) < 0.3]
    platform2_y = rng.choice(valid_p2_y)

    platform1 = Bar(
        x=MIN_X + platform1_x * WORLD_WIDTH,
        y=MIN_Y + platform1_y * WORLD_HEIGHT + bar_thickness / 2,
        length=platform_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    platform2 = Bar(
        x=MIN_X + platform2_x * WORLD_WIDTH,
        y=MIN_Y + platform2_y * WORLD_HEIGHT + bar_thickness / 2,
        length=platform_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    basket1, green_ball, obstacle1 = _jar_with_ball(platform1, right=False, ball_color="green")
    basket2, blue_ball, obstacle2 = _jar_with_ball(platform2, right=True, ball_color="blue")

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

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
        name="mouse_traps",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
