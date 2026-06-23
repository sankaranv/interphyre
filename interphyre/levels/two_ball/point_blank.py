import numpy as np
from interphyre.objects import Ball, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


def _create_element(cx, cy, left: bool):
    """Tilted bar channel with vertical blocker and dynamic handle.

    Replicates PHYRE task00123 _create_element exactly:
      - bottom_bar + top_bar: two parallel static bars at ±30°
      - blocker: static vertical Bar at the lower end of bottom_bar
      - ball: resting on top of blocker, wedged by the handle
      - handle: dynamic bar at the same angle, pressing against the ball laterally

    The ball is stable because the handle prevents it from rolling off the
    blocker sideways.  Player knocks the handle, ball falls, catches ramp catches it.

    Returns (ball, top_bar, blocker, handle).
    """
    bar_thickness = 0.2
    bar_length = 0.25 * WORLD_WIDTH   # = 2.5
    arm = bar_length / 2              # = 1.25
    angle = -30.0 if left else 30.0
    cos_a = np.cos(np.radians(abs(angle)))  # cos(30°) ≈ 0.866
    sin_a = np.sin(np.radians(abs(angle)))  # sin(30°) = 0.5

    # Signed cos/sin along bar direction for positioning.
    # bar at -30° (left): bar goes from upper-left to lower-right.
    # Rightmost vertex from center: (+arm*cos_a, -arm*sin_a) + perpendicular thickness.
    bar_right_from_center = arm * cos_a + bar_thickness / 2 * sin_a  # ≈ 1.133
    bar_bottom_from_center = arm * sin_a + bar_thickness / 2 * cos_a  # ≈ 0.712

    bottom_bar = Bar.from_point_and_angle(
        x=cx, y=cy,
        angle=angle,
        length=bar_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    top_bar = Bar.from_point_and_angle(
        x=cx, y=cy + 0.18 * WORLD_HEIGHT,
        angle=angle,
        length=bar_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Vertical blocker (scale=0.06 → length=0.6) at the lower end of bottom_bar.
    # PHYRE: bottom=bottom_bar.bottom, left=bottom_bar.right-0.02*W (left case).
    blocker_length = 0.06 * WORLD_WIDTH  # = 0.6
    blocker_bottom = cy - bar_bottom_from_center
    if left:
        blocker_left = cx + bar_right_from_center - 0.02 * WORLD_WIDTH
        blocker_x = blocker_left + bar_thickness / 2
    else:
        blocker_right = cx - bar_right_from_center + 0.02 * WORLD_WIDTH
        blocker_x = blocker_right - bar_thickness / 2

    blocker = Bar(
        bottom=blocker_bottom,
        top=blocker_bottom + blocker_length,
        x=blocker_x,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Ball resting on top of blocker.
    # PHYRE: ball.bottom=blocker.top, ball.right=blocker.left+0.02*W (left case).
    ball_radius = WORLD_WIDTH / 40  # = 0.25 (PHYRE scale=0.1 → 0.1*600/4/60)
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

    # Dynamic handle bar pressing against the ball laterally.
    # PHYRE: handle.center_y=cy+0.08*H, handle.right=ball.left (left case).
    # For bar at angle=-30°: handle.right = handle_cx + arm*cos_a + t/2*sin_a.
    handle_cy = cy + 0.08 * WORLD_HEIGHT
    handle_right_half = arm * cos_a + bar_thickness / 2 * sin_a  # = 1.083 + 0.05 = 1.133
    if left:
        handle_cx = (ball_x - ball_radius) - handle_right_half
    else:
        handle_cx = (ball_x + ball_radius) + handle_right_half

    handle = Bar.from_point_and_angle(
        x=handle_cx,
        y=handle_cy,
        angle=angle,
        length=bar_length,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )

    return ball, top_bar, blocker, handle


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

    green_ball, top_bar_1, blocker_1, handle_1 = _create_element(cx1, cy1, left=True)
    blue_ball, top_bar_2, blocker_2, handle_2 = _create_element(cx2, cy2, left=False)

    bar_thickness = 0.2

    # Catch ramps at the scene bottom — converging V-funnel to bring falling balls together.
    # PHYRE: scale=0.52, angle=±10°, bottom=0, left=-0.01*W / right=scene.width.
    ramp_length = 0.52 * WORLD_WIDTH  # = 5.2
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

    # Obstacle bars above each element's top_bar to block direct action-ball solutions.
    # PHYRE: scale=0.3, bottom=blocker.top + 0.1*H; right=blocker.left / left=blocker.right.
    obs_length = 0.3 * WORLD_WIDTH  # = 3.0
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
