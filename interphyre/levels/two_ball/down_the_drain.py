import numpy as np
from interphyre.objects import Ball, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MIN_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


def _create_structure(ball_x_frac, ball_y_frac, left: bool):
    """Ball rests on a horizontal dynamic stick (trap door). Knock the stick
    to release the ball into the V-ramp below where it meets the other ball."""
    bar_thickness = 0.2
    ball_radius = 0.1 * WORLD_WIDTH / 2

    ball_x = MIN_X + ball_x_frac * WORLD_WIDTH
    ball_y = MIN_Y + ball_y_frac * WORLD_HEIGHT

    # Horizontal dynamic stick supporting the ball from below.
    # Ball rests on stick.top; when stick is knocked sideways it slides out
    # and the ball falls to the drain below.
    stick_length = 0.2 * WORLD_WIDTH
    stick_cy = (ball_y - ball_radius) - bar_thickness / 2
    if left:
        # Ball sits at the right end of the stick (stick extends leftward).
        stick_right = ball_x + ball_radius
        stick_left = stick_right - stick_length
    else:
        # Ball sits at the left end of the stick (stick extends rightward).
        stick_left = ball_x - ball_radius
        stick_right = stick_left + stick_length
    stick = Bar(
        left=stick_left,
        right=stick_right,
        y=stick_cy,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )

    # Short horizontal ceiling bar just above the ball — constrains upward bounce
    # and forms the "second tiny bar" visible alongside the stick.
    top_bar_length = 0.1 * WORLD_WIDTH
    if left:
        top_bar_cx = ball_x + ball_radius - top_bar_length / 2
    else:
        top_bar_cx = ball_x - ball_radius + top_bar_length / 2
    top_bar_cy = (ball_y + ball_radius + 0.01 * WORLD_HEIGHT) + bar_thickness / 2
    top_bar = Bar(
        left=top_bar_cx - top_bar_length / 2,
        right=top_bar_cx + top_bar_length / 2,
        y=top_bar_cy,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Full-height vertical wall at the outer end of the stick. The stick's
    # outer end presses against this wall (friction keeps stick up until knocked).
    wall_length = WORLD_WIDTH
    if left:
        wall_cx = stick.right + bar_thickness / 2
    else:
        wall_cx = stick.left - bar_thickness / 2
    wall_top = stick.top
    vertical_wall = Bar(
        top=wall_top,
        bottom=wall_top - wall_length,
        x=wall_cx,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    ball = Ball(
        x=ball_x, y=ball_y, radius=ball_radius,
        color="green" if left else "blue",
        dynamic=True,
    )

    return ball, vertical_wall, top_bar, stick


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

    (green_ball, vertical_wall_1, top_bar_1, stick_1) = \
        _create_structure(ball1_x, ball1_y, left=True)
    (blue_ball, vertical_wall_2, top_bar_2, stick_2) = \
        _create_structure(ball2_x, ball2_y, left=False)

    bar_thickness = 0.2
    # Catch ramps at the floor between the two walls, forming a V-funnel so
    # falling balls converge in the middle.
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
        "top_bar_1": top_bar_1,
        "top_bar_2": top_bar_2,
        "stick_1": stick_1,
        "stick_2": stick_2,
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
