import numpy as np
from interphyre.objects import Ball, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    dist_options = np.linspace(0.05, 0.15, 3)   # [0.05, 0.10, 0.15]
    size_options = np.linspace(0.6, 0.8, 4)      # [0.6, 0.667, 0.733, 0.8]
    height_options = np.linspace(0.0, 0.3, 6)    # [0.0, 0.06, ..., 0.3]

    bar_thickness = 0.2
    ball_radius = 0.1 * WORLD_WIDTH / 2

    # Constraint: if size==0.8 then left_d + right_d must be < 0.2.
    size = rng.choice(size_options)
    left_d = rng.choice(dist_options)
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

    # Approximate standingsticks with nearly-vertical dynamic bars.
    stick_length = size * WORLD_WIDTH
    left_stick_x = MIN_X + left_d * WORLD_WIDTH
    right_stick_x = MIN_X + (1.0 - right_d) * WORLD_WIDTH
    left_stick = Bar(
        top=ground.top + stick_length,
        bottom=ground.top,
        x=left_stick_x,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )
    right_stick = Bar(
        top=ground.top + stick_length,
        bottom=ground.top,
        x=right_stick_x,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )
    stick_top = ground.top + stick_length

    green_ball = Ball(
        x=left_stick_x + ball_radius + bar_thickness / 2,
        y=stick_top + ball_radius,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )
    blue_ball = Ball(
        x=right_stick_x - ball_radius - bar_thickness / 2,
        y=stick_top + ball_radius,
        radius=ball_radius,
        color="blue",
        dynamic=True,
    )

    slope_scale = 0.25 / ((left_d + right_d) / 0.2) if (left_d + right_d) > 0.2 else 0.3
    slope_length = slope_scale * WORLD_WIDTH
    slope_left = Bar.from_point_and_angle(
        x=left_stick.right + slope_length / 2 * np.cos(np.radians(10.0)),
        y=stick_top - bar_thickness / 2 - slope_length / 2 * np.sin(np.radians(10.0)),
        length=slope_length,
        angle=-10.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    slope_right = Bar.from_point_and_angle(
        x=right_stick.left - slope_length / 2 * np.cos(np.radians(10.0)),
        y=stick_top - bar_thickness / 2 - slope_length / 2 * np.sin(np.radians(10.0)),
        length=slope_length,
        angle=10.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    base_slope_length = 0.25 * WORLD_WIDTH
    cos30 = np.cos(np.radians(30.0))
    sin30 = np.sin(np.radians(30.0))
    base_left = Bar.from_point_and_angle(
        x=left_stick_x + base_slope_length / 2 * cos30,
        y=ground.top + base_slope_length / 2 * sin30,
        length=base_slope_length,
        angle=30.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    base_right = Bar.from_point_and_angle(
        x=right_stick_x - base_slope_length / 2 * cos30,
        y=ground.top + base_slope_length / 2 * sin30,
        length=base_slope_length,
        angle=-30.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    border = Bar(
        left=MIN_X,
        right=MIN_X + WORLD_WIDTH,
        y=blue_ball.y + blue_ball.radius + bar_thickness / 2 + 0.33,
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
        "left_stick": left_stick,
        "right_stick": right_stick,
        "slope_left": slope_left,
        "slope_right": slope_right,
        "base_left": base_left,
        "base_right": base_right,
        "border": border,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00111",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
