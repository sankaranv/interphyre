import numpy as np
from interphyre.objects import Ball, Bar, Cross
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


def _cross_extents(arm_length, body_angle_deg, spread_deg):
    """Bounding-box half-extents (max_x, max_y) of a Cross from its body center."""
    ba = np.radians(body_angle_deg)
    sr = np.radians(spread_deg)
    a1, a2 = ba + sr, ba - sr
    max_x = arm_length * max(abs(np.cos(a1)), abs(np.cos(a2)))
    max_y = arm_length * max(abs(np.sin(a1)), abs(np.sin(a2)))
    return max_x, max_y


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    dist_options = np.linspace(0.05, 0.15, 3)
    size_options = np.linspace(0.6, 0.8, 4)
    height_options = np.linspace(0.0, 0.3, 6)

    bar_thickness = 0.2
    # PHYRE ball scale=0.1 → radius = scale * SCENE_WIDTH / 4 = 0.1 * 600 / 4 / 60 = 0.25
    ball_radius = WORLD_WIDTH / 40  # = 0.25

    size = rng.choice(size_options)
    # PHYRE skips seeds where size==0.8 and left_d+right_d>=0.2.  Filter left_d first
    # so there is always at least one valid right_d to choose from.
    valid_left_d = [
        l for l in dist_options
        if any(not (size == 0.8 and l + r >= 0.2) for r in dist_options)
    ]
    left_d = rng.choice(valid_left_d)
    valid_right_d = [r for r in dist_options if not (size == 0.8 and left_d + r >= 0.2)]
    right_d = rng.choice(valid_right_d)
    ground_y = rng.choice(height_options)

    ground = Bar(
        left=MIN_X,
        right=MIN_X + WORLD_WIDTH,
        y=MIN_Y + ground_y * WORLD_HEIGHT + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Left standingstick: body_angle=-20°, bars spread 77.5° from bisector.
    # In PHYRE: bottom=ground.top, left=left_d*scene.width, angle=-20.
    spread = 77.5
    arm_length = size * WORLD_WIDTH / 3

    left_ext_x, left_ext_y = _cross_extents(arm_length, -20.0, spread)
    left_body_x = MIN_X + left_d * WORLD_WIDTH + left_ext_x
    left_body_y = ground.top + left_ext_y

    left_cross = Cross(
        x=left_body_x,
        y=left_body_y,
        angle=-20.0,
        spread=spread,
        arm_length=arm_length,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )

    # Right standingstick: body_angle=+20°, mirror of left.
    # In PHYRE: bottom=ground.top, right=(1-right_d)*scene.width, angle=+20.
    right_ext_x, right_ext_y = _cross_extents(arm_length, 20.0, spread)
    right_body_x = MIN_X + (1 - right_d) * WORLD_WIDTH - right_ext_x
    right_body_y = ground.top + right_ext_y

    right_cross = Cross(
        x=right_body_x,
        y=right_body_y,
        angle=20.0,
        spread=spread,
        arm_length=arm_length,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )

    # Balls nestle inside the V formed by the upper arms of each standingstick.
    # The two upper arms are always 25° apart (= 180° - 2*spread = 180 - 155 = 25°),
    # so the ball settles at h = (ball_radius + bar_thickness/2) / sin(12.5°) above
    # the body center along the bisector direction.
    contact_dist = ball_radius + bar_thickness / 2  # 0.35
    half_angle = 12.5  # degrees — fixed by spread=77.5
    h_bisector = contact_dist / np.sin(np.radians(half_angle))

    # Left cross (angle=-20): upper arms at 57.5° and 82.5°; bisector at 70°.
    left_bisector = 70.0
    green_ball = Ball(
        x=left_body_x + h_bisector * np.cos(np.radians(left_bisector)),
        y=left_body_y + h_bisector * np.sin(np.radians(left_bisector)),
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    # Right cross (angle=+20): upper arms at 97.5° and 122.5°; bisector at 110°.
    right_bisector = 110.0
    blue_ball = Ball(
        x=right_body_x + h_bisector * np.cos(np.radians(right_bisector)),
        y=right_body_y + h_bisector * np.sin(np.radians(right_bisector)),
        radius=ball_radius,
        color="blue",
        dynamic=True,
    )

    # Inner slopes connecting the two standingsticks at mid-height.
    # In PHYRE: slope_left.left=left.right, slope_left.top≈right.top; angle=-10.
    slope_scale_val = 0.25 / ((left_d + right_d) / 0.2) if (left_d + right_d) > 0.2 else 0.3
    slope_length = slope_scale_val * WORLD_WIDTH
    cos10 = np.cos(np.radians(10.0))
    sin10 = np.sin(np.radians(10.0))

    left_cross_right = left_body_x + left_ext_x
    right_cross_top = right_body_y + right_ext_y
    left_cross_top = left_body_y + left_ext_y
    right_cross_left = right_body_x - right_ext_x

    slope_left = Bar.from_point_and_angle(
        x=left_cross_right + slope_length / 2 * cos10,
        y=right_cross_top - slope_length / 2 * sin10,
        length=slope_length,
        angle=-10.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    slope_right = Bar.from_point_and_angle(
        x=right_cross_left - slope_length / 2 * cos10,
        y=left_cross_top - slope_length / 2 * sin10,
        length=slope_length,
        angle=10.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Base slopes adjacent to each standingstick to guide action balls toward them.
    # In PHYRE: left=left.center_x-5px, bottom=ground.top, angle=30.
    base_slope_length = 0.25 * WORLD_WIDTH
    cos30 = np.cos(np.radians(30.0))
    sin30 = np.sin(np.radians(30.0))

    base_left = Bar.from_point_and_angle(
        x=left_body_x + base_slope_length / 2 * cos30,
        y=ground.top + base_slope_length / 2 * sin30,
        length=base_slope_length,
        angle=30.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    base_right = Bar.from_point_and_angle(
        x=right_body_x - base_slope_length / 2 * cos30,
        y=ground.top + base_slope_length / 2 * sin30,
        length=base_slope_length,
        angle=-30.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Border bar above both balls to prevent trivial action-ball drop solutions.
    cross_top = max(left_cross_top, right_cross_top)
    ball_top = cross_top + h_bisector * np.sin(np.radians(70.0)) + ball_radius
    border = Bar(
        left=MIN_X,
        right=MIN_X + WORLD_WIDTH,
        y=ball_top + 0.333 + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "green_ball": green_ball,
        "blue_ball": blue_ball,
        "ground": ground,
        "left_cross": left_cross,
        "right_cross": right_cross,
        "slope_left": slope_left,
        "slope_right": slope_right,
        "base_left": base_left,
        "base_right": base_right,
        "border": border,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="star_crossed",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
