import numpy as np
from interphyre.objects import Ball, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MIN_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


def _create_structure(ball_x_frac, ball_y_frac, left: bool):
    """Build a Goldberg-machine structure: ball in alley, topplable stick, vertical wall."""
    bar_thickness = 0.2
    ball_radius = 0.1 * WORLD_WIDTH / 2

    ball_x = MIN_X + ball_x_frac * WORLD_WIDTH
    ball_y = MIN_Y + ball_y_frac * WORLD_HEIGHT

    # Horizontal shelf just below the ball.
    bottom_bar_length = 0.2 * WORLD_WIDTH
    if left:
        bottom_bar_cx = ball_x + ball_radius - bottom_bar_length / 2
    else:
        bottom_bar_cx = ball_x - ball_radius + bottom_bar_length / 2
    bottom_bar_cy = (ball_y - ball_radius) - bar_thickness / 2
    bottom_bar = Bar(
        left=bottom_bar_cx - bottom_bar_length / 2,
        right=bottom_bar_cx + bottom_bar_length / 2,
        y=bottom_bar_cy,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Thin shelf just above the ball, creating a narrow alley that traps the ball
    # until the stick falls.
    top_bar_length = 0.1 * WORLD_WIDTH
    if left:
        top_bar_cx = ball_x + ball_radius - top_bar_length / 2
    else:
        top_bar_cx = bottom_bar.left + top_bar_length / 2
    top_bar_cy = (ball_y + ball_radius + 0.01 * WORLD_HEIGHT) + bar_thickness / 2
    top_bar = Bar(
        left=top_bar_cx - top_bar_length / 2,
        right=top_bar_cx + top_bar_length / 2,
        y=top_bar_cy,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Dynamic stick standing at the inner edge of the bottom shelf. When toppled,
    # it releases the ball from the alley.
    stick_length = 0.12 * WORLD_WIDTH
    stick_cx = bottom_bar.left + bar_thickness / 2 if left else bottom_bar.right - bar_thickness / 2
    stick_bottom = bottom_bar.top
    stick = Bar(
        top=stick_bottom + stick_length,
        bottom=stick_bottom,
        x=stick_cx,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )

    # Full-height vertical wall at the outer edge of the bottom shelf.
    wall_length = WORLD_WIDTH
    wall_cx = bottom_bar.right - bar_thickness / 2 if left else bottom_bar.left + bar_thickness / 2
    wall_top = bottom_bar.top
    vertical_wall = Bar(
        top=wall_top,
        bottom=wall_top - wall_length,
        x=wall_cx,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Short horizontal bumper above the stick, flush with the stick's outer edge
    # so it doesn't poke out beyond the alley boundary. Placed at the same height
    # as the original vertical bumper (stick.top + 0.2 * WORLD_HEIGHT) but now
    # oriented horizontally and extending inward from the stick's outer face.
    bumper_length = 0.1 * WORLD_WIDTH
    bumper_y = stick.top + 0.2 * WORLD_HEIGHT
    if left:
        bumper = Bar(
            left=stick.left,
            right=stick.left + bumper_length,
            y=bumper_y,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )
    else:
        bumper = Bar(
            left=stick.right - bumper_length,
            right=stick.right,
            y=bumper_y,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )

    ball = Ball(
        x=ball_x, y=ball_y, radius=ball_radius,
        color="green" if left else "blue",
        dynamic=True,
    )

    return ball, vertical_wall, bottom_bar, top_bar, stick, bumper


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    ball_x_options = [0.1 * val for val in range(2, 8)]  # 0.2..0.7
    ball_y_options = [0.1 * val for val in range(2, 8)]  # 0.2..0.7

    # ball2_x - ball1_x >= 0.3: filter ball1_x first to guarantee a valid ball2_x.
    valid_ball1_x = [x for x in ball_x_options if any(p - x >= 0.3 for p in ball_x_options)]
    ball1_x = rng.choice(valid_ball1_x)
    valid_ball2_x = [x for x in ball_x_options if x - ball1_x >= 0.3]
    ball2_x = rng.choice(valid_ball2_x)
    ball1_y = rng.choice(ball_y_options)
    ball2_y = rng.choice(ball_y_options)

    (green_ball, vertical_wall_1, bottom_bar_1, top_bar_1, stick_1, bumper_1) = \
        _create_structure(ball1_x, ball1_y, left=True)
    (blue_ball, vertical_wall_2, bottom_bar_2, top_bar_2, stick_2, bumper_2) = \
        _create_structure(ball2_x, ball2_y, left=False)

    bar_thickness = 0.2
    # Catch ramps at the floor between the two walls, forming a V-funnel.
    ramp_scale = (vertical_wall_2.left - vertical_wall_1.right) / (2.0 * WORLD_WIDTH)
    ramp_length = ramp_scale * WORLD_WIDTH
    ramp_bottom = MIN_Y - 0.015 * WORLD_HEIGHT
    half_sin = (ramp_length / 2) * np.sin(np.radians(10.0))
    half_cos = (ramp_length / 2) * np.cos(np.radians(10.0))
    left_ramp = Bar.from_point_and_angle(
        x=vertical_wall_1.left + half_cos,
        y=ramp_bottom + half_sin,
        angle=-10.0,
        length=ramp_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_ramp = Bar.from_point_and_angle(
        x=vertical_wall_2.right - half_cos,
        y=ramp_bottom + half_sin,
        angle=10.0,
        length=ramp_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "green_ball": green_ball,
        "blue_ball": blue_ball,
        "vertical_wall_1": vertical_wall_1,
        "vertical_wall_2": vertical_wall_2,
        "bottom_bar_1": bottom_bar_1,
        "bottom_bar_2": bottom_bar_2,
        "top_bar_1": top_bar_1,
        "top_bar_2": top_bar_2,
        "stick_1": stick_1,
        "stick_2": stick_2,
        "bumper_1": bumper_1,
        "bumper_2": bumper_2,
        "left_ramp": left_ramp,
        "right_ramp": right_ramp,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="down_the_drain",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
