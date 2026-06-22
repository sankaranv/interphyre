import numpy as np
from interphyre.objects import Ball, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


def _create_element(cx, cy, left: bool):
    """Tilted bar structure with a ball perched on a vertical blocker.

    Returns (ball, top_bar) where top_bar is used to place the obstacle above.
    """
    bar_thickness = 0.2
    bar_length = 0.25 * WORLD_WIDTH   # = 2.5
    bar_half = bar_length / 2         # = 1.25
    cos30 = np.cos(np.radians(30.0))  # ≈ 0.866
    sin30 = np.sin(np.radians(30.0))  # = 0.5
    half_proj_x = bar_half * cos30    # ≈ 1.083
    half_proj_y = bar_half * sin30    # = 0.625
    angle = -30.0 if left else 30.0

    # Two parallel tilted bars framing the structure.
    bottom_bar = Bar.from_point_and_angle(
        x=cx, y=cy, angle=angle,
        length=bar_length, thickness=bar_thickness,
        color="black", dynamic=False,
    )
    top_bar = Bar.from_point_and_angle(
        x=cx, y=cy + 0.18 * WORLD_HEIGHT, angle=angle,
        length=bar_length, thickness=bar_thickness,
        color="black", dynamic=False,
    )

    # Vertical blocker: sits at the lower end of bottom_bar, holds the ball.
    blocker_length = 0.06 * WORLD_WIDTH  # = 0.6
    blocker_bottom = cy - half_proj_y    # = bottom of bottom_bar's lower end
    if left:
        # set_left(bottom_bar.right - 0.02*W): left edge at cx+half_proj_x-0.02*W
        blocker_left = cx + half_proj_x - 0.02 * WORLD_WIDTH
        blocker_cx = blocker_left + bar_thickness / 2
    else:
        # set_right(bottom_bar.left + 0.02*W): right edge at cx-half_proj_x+0.02*W
        blocker_right = cx - half_proj_x + 0.02 * WORLD_WIDTH
        blocker_cx = blocker_right - bar_thickness / 2
    blocker = Bar(
        top=blocker_bottom + blocker_length,
        bottom=blocker_bottom,
        x=blocker_cx,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Ball resting on top of blocker, nudged toward the structure.
    ball_radius = 0.1 * WORLD_WIDTH / 2  # = 0.5
    ball_y = blocker.top + ball_radius
    if left:
        # set_right(blocker.left + 0.02*W): ball center_x = blocker.left+0.02*W - radius
        ball_x = blocker.left + 0.02 * WORLD_WIDTH - ball_radius
    else:
        # set_left(blocker.right - 0.02*W): ball center_x = blocker.right-0.02*W + radius
        ball_x = blocker.right - 0.02 * WORLD_WIDTH + ball_radius
    ball = Ball(
        x=ball_x, y=ball_y, radius=ball_radius,
        color="green" if left else "blue",
        dynamic=True,
    )

    # Dynamic handle bar that can be tipped to release the ball.
    handle_length = 0.25 * WORLD_WIDTH  # = 2.5
    handle_cx = (
        (ball_x - ball_radius) - handle_length / 2 * cos30   # set_right(ball.left)
        if left else
        (ball_x + ball_radius) + handle_length / 2 * cos30   # set_left(ball.right)
    )
    handle = Bar.from_point_and_angle(
        x=handle_cx, y=cy + 0.08 * WORLD_HEIGHT,
        angle=angle, length=handle_length, thickness=bar_thickness,
        color="gray", dynamic=True,
    )

    return ball, top_bar, handle


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    center_x_options = np.linspace(0.3, 0.7, 10)
    center_y_options = np.linspace(0.3, 0.7, 10)

    # center2_x - center1_x > 0.35: filter center1_x to guarantee a valid center2_x.
    valid_c1x = [x for x in center_x_options if any(p - x > 0.35 for p in center_x_options)]
    c1_x_frac = rng.choice(valid_c1x)
    valid_c2x = [x for x in center_x_options if x - c1_x_frac > 0.35]
    c2_x_frac = rng.choice(valid_c2x)
    c1_y_frac = rng.choice(center_y_options)
    c2_y_frac = rng.choice(center_y_options)

    cx1 = MIN_X + c1_x_frac * WORLD_WIDTH
    cy1 = MIN_Y + c1_y_frac * WORLD_HEIGHT
    cx2 = MIN_X + c2_x_frac * WORLD_WIDTH
    cy2 = MIN_Y + c2_y_frac * WORLD_HEIGHT

    green_ball, top_bar_1, handle_1 = _create_element(cx1, cy1, left=True)
    blue_ball, top_bar_2, handle_2 = _create_element(cx2, cy2, left=False)

    bar_thickness = 0.2
    bar_half_proj = (0.25 * WORLD_WIDTH / 2) * np.cos(np.radians(30.0))  # ≈ 1.083
    top_bar_top = 0.625  # (bar_half * sin30) for bars 0.18*H above cy

    # Obstacle bars above each top_bar to block simple solutions.
    # scale=0.3 → length=3.0; bottom=top.top+0.1*H; right=top.left (left) or left=top.right (right).
    obs_length = 0.3 * WORLD_WIDTH  # = 3.0
    obs1_top_y = cy1 + 0.18 * WORLD_HEIGHT + top_bar_top + 0.1 * WORLD_HEIGHT
    obs1 = Bar(
        left=cx1 - bar_half_proj - obs_length,
        right=cx1 - bar_half_proj,
        y=obs1_top_y + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    obs2_top_y = cy2 + 0.18 * WORLD_HEIGHT + top_bar_top + 0.1 * WORLD_HEIGHT
    obs2 = Bar(
        left=cx2 + bar_half_proj,
        right=cx2 + bar_half_proj + obs_length,
        y=obs2_top_y + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Large catch ramps at the floor (scale=0.52, angle=±10°, bottom=0=MIN_Y).
    ramp_length = 0.52 * WORLD_WIDTH  # = 5.2
    ramp_half_sin = (ramp_length / 2) * np.sin(np.radians(10.0))
    ramp_half_cos = (ramp_length / 2) * np.cos(np.radians(10.0))
    left_ramp = Bar.from_point_and_angle(
        x=MIN_X + ramp_half_cos,
        y=MIN_Y + ramp_half_sin,
        angle=-10.0,
        length=ramp_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_ramp = Bar.from_point_and_angle(
        x=MAX_X - ramp_half_cos,
        y=MIN_Y + ramp_half_sin,
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
        "top_bar_1": top_bar_1,
        "top_bar_2": top_bar_2,
        "handle_1": handle_1,
        "handle_2": handle_2,
        "obstacle_1": obs1,
        "obstacle_2": obs2,
        "left_ramp": left_ramp,
        "right_ramp": right_ramp,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00123",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
