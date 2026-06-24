import numpy as np
from interphyre.objects import Ball, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


def _build_ramp_channel(center_x, center_y, left: bool):
    """Tilted ramp channel with vertical blocker and dynamic handle.

    Two parallel static bars form a tilted ramp channel at ±30°; a vertical blocker
    at the lower end supports a dynamic ball; a dynamic handle presses against
    the ball laterally, keeping it from rolling off the blocker. Knocking the
    handle drops the ball down the channel.

    Returns (ball, bottom_bar, top_bar, blocker, handle).
    """
    bar_thickness = 0.2
    bar_length = 0.25 * WORLD_WIDTH
    half_length = bar_length / 2
    angle = -30.0 if left else 30.0
    cos_a = np.cos(np.radians(abs(angle)))  # cos(30°) ≈ 0.866
    sin_a = np.sin(np.radians(abs(angle)))  # sin(30°) = 0.5

    # Axis-aligned extents from the bar center to its lowest/outermost corner,
    # used to position the blocker flush with the bottom end of the ramp.
    bar_half_width = half_length * cos_a + bar_thickness / 2 * sin_a
    bar_half_height = half_length * sin_a + bar_thickness / 2 * cos_a

    bottom_bar = Bar.from_point_and_angle(
        x=center_x, y=center_y,
        angle=angle,
        length=bar_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    top_bar = Bar.from_point_and_angle(
        x=center_x, y=center_y + 0.18 * WORLD_HEIGHT,
        angle=angle,
        length=bar_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Vertical blocker at the lower end of the bottom ramp bar, just inside its outer edge.
    blocker_length = 0.06 * WORLD_WIDTH
    blocker_bottom = center_y - bar_half_height
    if left:
        blocker_left = center_x + bar_half_width - 0.02 * WORLD_WIDTH
        blocker_x = blocker_left + bar_thickness / 2
    else:
        blocker_right = center_x - bar_half_width + 0.02 * WORLD_WIDTH
        blocker_x = blocker_right - bar_thickness / 2

    blocker = Bar(
        bottom=blocker_bottom,
        top=blocker_bottom + blocker_length,
        x=blocker_x,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Ball resting on top of the blocker, positioned just inside the blocker edge.
    ball_radius = WORLD_WIDTH / 40
    ball_y = blocker.top + ball_radius
    if left:
        ball_x = blocker.left + 0.02 * WORLD_WIDTH - ball_radius
    else:
        ball_x = blocker.right - 0.02 * WORLD_WIDTH + ball_radius

    ball = Ball(
        x=ball_x,
        y=ball_y,
        radius=ball_radius,
        color="green" if left else "blue",
        dynamic=True,
    )

    # Dynamic handle bar pressing against the ball laterally. The handle's far edge
    # just touches the ball so the ball is sandwiched between the handle and blocker.
    handle_cy = center_y + 0.08 * WORLD_HEIGHT
    handle_half_width = half_length * cos_a + bar_thickness / 2 * sin_a
    if left:
        handle_cx = (ball_x - ball_radius) - handle_half_width
    else:
        handle_cx = (ball_x + ball_radius) + handle_half_width

    handle = Bar.from_point_and_angle(
        x=handle_cx,
        y=handle_cy,
        angle=angle,
        length=bar_length,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )

    return ball, bottom_bar, top_bar, blocker, handle


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    center_x_options = np.linspace(0.3, 0.7, 10)
    center_y_options = np.linspace(0.3, 0.7, 10)

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

    green_ball, bottom_bar_1, top_bar_1, blocker_1, handle_1 = _build_ramp_channel(cx1, cy1, left=True)
    blue_ball, bottom_bar_2, top_bar_2, blocker_2, handle_2 = _build_ramp_channel(cx2, cy2, left=False)

    bar_thickness = 0.2

    # Catch ramps at the scene bottom — converging V-funnel to bring falling balls together.
    ramp_length = 0.52 * WORLD_WIDTH
    cos10 = np.cos(np.radians(10.0))
    sin10 = np.sin(np.radians(10.0))
    ramp_cy = MIN_Y + ramp_length / 2 * sin10 + bar_thickness / 2 * cos10

    left_ramp = Bar.from_point_and_angle(
        x=MIN_X + ramp_length / 2 * cos10,
        y=ramp_cy,
        angle=-10.0,
        length=ramp_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_ramp = Bar.from_point_and_angle(
        x=MAX_X - ramp_length / 2 * cos10,
        y=ramp_cy,
        angle=10.0,
        length=ramp_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Obstacle bars above each blocker to prevent direct action-ball solutions.
    # Each obstacle extends 0.3*WORLD_WIDTH inward from the blocker edge.
    obs_length = 0.3 * WORLD_WIDTH
    obs1_y = blocker_1.top + 0.1 * WORLD_HEIGHT + bar_thickness / 2
    obs1 = Bar(
        left=blocker_1.x - bar_thickness / 2 - obs_length,
        right=blocker_1.x - bar_thickness / 2,
        y=obs1_y,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    obs2_y = blocker_2.top + 0.1 * WORLD_HEIGHT + bar_thickness / 2
    obs2 = Bar(
        left=blocker_2.x + bar_thickness / 2,
        right=blocker_2.x + bar_thickness / 2 + obs_length,
        y=obs2_y,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "green_ball": green_ball,
        "blue_ball": blue_ball,
        "bottom_bar_1": bottom_bar_1,
        "bottom_bar_2": bottom_bar_2,
        "top_bar_1": top_bar_1,
        "top_bar_2": top_bar_2,
        "blocker_1": blocker_1,
        "blocker_2": blocker_2,
        "handle_1": handle_1,
        "handle_2": handle_2,
        "left_ramp": left_ramp,
        "right_ramp": right_ramp,
        "obstacle_1": obs1,
        "obstacle_2": obs2,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="point_blank",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
