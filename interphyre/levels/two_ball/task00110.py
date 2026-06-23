import numpy as np
from interphyre.objects import Ball, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    step_size = 0.1
    platform_x_options = [step_size * val for val in range(1, 9)]  # 0.1..0.8
    platform_y_options = [step_size * val for val in range(4, 8)]  # 0.4..0.7

    bar_thickness = 0.2
    platform_length = 0.1 * WORLD_WIDTH
    ball_radius = 0.1 * WORLD_WIDTH / 2

    # Both SkipTemplateParams conditions reduce to platform2_x - platform1_x >= 0.32:
    # (1) gap > 2.5*step_size=0.25; (2) separator hole >= 2*ball_radius ≈ 0.32.
    valid_p1_x = [x for x in platform_x_options if any(p - x >= 0.32 for p in platform_x_options)]
    platform1_x = rng.choice(valid_p1_x)
    valid_p2_x = [x for x in platform_x_options if x - platform1_x >= 0.32]
    platform2_x = rng.choice(valid_p2_x)

    platform1_y = rng.choice(platform_y_options)
    platform2_y = rng.choice(platform_y_options)
    peak_on_left = rng.choice([True, False])

    platform1_left = MIN_X + platform1_x * WORLD_WIDTH
    platform1 = Bar(
        left=platform1_left,
        right=platform1_left + platform_length,
        y=MIN_Y + platform1_y * WORLD_HEIGHT + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    platform2_left = MIN_X + platform2_x * WORLD_WIDTH
    platform2 = Bar(
        left=platform2_left,
        right=platform2_left + platform_length,
        y=MIN_Y + platform2_y * WORLD_HEIGHT + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    green_ball = Ball(
        x=(platform1.left + platform1.right) / 2,
        y=platform1.top + ball_radius,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )
    blue_ball = Ball(
        x=(platform2.left + platform2.right) / 2,
        y=platform2.top + ball_radius,
        radius=ball_radius,
        color="blue",
        dynamic=True,
    )

    sep_length = (1.0 - min(platform1_y, platform2_y)) * WORLD_HEIGHT
    sep_x = platform1.right + (platform2.left - platform1.right) / 2
    separator = Bar(
        top=MAX_Y,
        bottom=MAX_Y - sep_length,
        x=sep_x,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Two long floor bars forming a tent peak at the target-ball's platform center.
    peak_x = green_ball.x if peak_on_left else blue_ball.x
    floor_length = 1.0 * WORLD_WIDTH
    half_span = (floor_length / 2) * np.cos(np.radians(5.0))
    floor_y = MIN_Y + bar_thickness / 2
    left_floor = Bar.from_point_and_angle(
        x=peak_x - half_span,
        y=floor_y,
        length=floor_length,
        angle=5.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_floor = Bar.from_point_and_angle(
        x=peak_x + half_span,
        y=floor_y,
        length=floor_length,
        angle=-5.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "green_ball": green_ball,
        "blue_ball": blue_ball,
        "platform_1": platform1,
        "platform_2": platform2,
        "separator": separator,
        "left_floor": left_floor,
        "right_floor": right_floor,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00110",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
