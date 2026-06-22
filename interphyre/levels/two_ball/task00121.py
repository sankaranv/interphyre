import numpy as np
from interphyre.objects import Ball, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


def _create_structure(ball_x_frac, ball_y_frac, left: bool):
    """Build a Goldberg-machine structure: ball in alley, topplable stick, vertical wall."""
    bar_thickness = 0.2
    ball_radius = 0.1 * WORLD_WIDTH / 2  # = 0.5

    ball_x = MIN_X + ball_x_frac * WORLD_WIDTH
    ball_y = MIN_Y + ball_y_frac * WORLD_HEIGHT

    # Horizontal shelf just below ball (set_right/set_left to align with ball edge).
    bottom_bar_length = 0.2 * WORLD_WIDTH  # = 2.0
    if left:
        # set_right(ball.right): right edge at ball.x+radius → center = ball.x+radius-length/2
        bottom_bar_cx = ball_x + ball_radius - bottom_bar_length / 2
    else:
        # set_left(ball.left): left edge at ball.x-radius → center = ball.x-radius+length/2
        bottom_bar_cx = ball_x - ball_radius + bottom_bar_length / 2
    # set_top(ball.bottom): top of bar at ball.y-radius
    bottom_bar_cy = (ball_y - ball_radius) - bar_thickness / 2
    bottom_bar = Bar(
        left=bottom_bar_cx - bottom_bar_length / 2,
        right=bottom_bar_cx + bottom_bar_length / 2,
        y=bottom_bar_cy,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Thin shelf just above ball.
    top_bar_length = 0.1 * WORLD_WIDTH  # = 1.0
    if left:
        # set_right(ball.right): center_x = ball.x+radius-top_bar_length/2
        top_bar_cx = ball_x + ball_radius - top_bar_length / 2
    else:
        # set_left(bottom_bar.left): center_x = bottom_bar.left+top_bar_length/2
        top_bar_cx = bottom_bar.left + top_bar_length / 2
    # set_bottom(ball.top + 0.01*H): bottom at ball.y+radius+0.1 → center above
    top_bar_cy = (ball_y + ball_radius + 0.01 * WORLD_HEIGHT) + bar_thickness / 2
    top_bar = Bar(
        left=top_bar_cx - top_bar_length / 2,
        right=top_bar_cx + top_bar_length / 2,
        y=top_bar_cy,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Dynamic stick standing at inner edge of bottom shelf.
    stick_length = 0.12 * WORLD_WIDTH  # = 1.2
    # set_left(bottom_bar.left) for left, set_right(bottom_bar.right) for right
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

    # Full-height vertical wall at outer edge of bottom shelf, going downward from shelf.
    wall_length = WORLD_WIDTH  # scale=1.0 → 10 units
    wall_cx = bottom_bar.right - bar_thickness / 2 if left else bottom_bar.left + bar_thickness / 2
    # set_top(bottom_bar.top): top at bottom_bar.top, wall extends downward
    wall_top = bottom_bar.top
    vertical_wall = Bar(
        top=wall_top,
        bottom=wall_top - wall_length,
        x=wall_cx,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Short vertical bar above stick (bumper that ball gets pushed against).
    bumper_length = 0.1 * WORLD_WIDTH  # = 1.0
    bumper_cx = stick.left + bar_thickness / 2 if left else stick.right - bar_thickness / 2
    # set_bottom(stick.top + 0.2*H): bottom at stick.top + 2.0
    bumper_bottom = stick.top + 0.2 * WORLD_HEIGHT
    bumper = Bar(
        top=bumper_bottom + bumper_length,
        bottom=bumper_bottom,
        x=bumper_cx,
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
    rng = np.random.default_rng(seed)

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
    # Catch ramps at the floor between the two walls (set_left/set_right + set_bottom(-0.015*H)).
    ramp_scale = (vertical_wall_2.left - vertical_wall_1.right) / (2.0 * WORLD_WIDTH)
    ramp_length = ramp_scale * WORLD_WIDTH
    ramp_bottom = MIN_Y - 0.015 * WORLD_HEIGHT  # slightly below floor
    half_sin = (ramp_length / 2) * np.sin(np.radians(10.0))
    half_cos = (ramp_length / 2) * np.cos(np.radians(10.0))
    # Left ramp: set_left(vertical_wall_1.left), angle=-10
    left_ramp = Bar.from_point_and_angle(
        x=vertical_wall_1.left + half_cos,
        y=ramp_bottom + half_sin,
        angle=-10.0,
        length=ramp_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    # Right ramp: set_right(vertical_wall_2.right), angle=10
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
        name="task00121",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
