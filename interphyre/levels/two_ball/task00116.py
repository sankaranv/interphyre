import numpy as np
from interphyre.objects import Ball, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_ground", success_time
    )


def _make_catapult(horizontal_position, height, line_width, dynamic_swing_base_ball):
    bar_thickness = 0.2
    base_length = 0.1 * WORLD_WIDTH
    base_x = MIN_X + horizontal_position * WORLD_WIDTH
    base = Bar(
        top=MIN_Y + height * WORLD_HEIGHT + base_length,
        bottom=MIN_Y + height * WORLD_HEIGHT,
        x=base_x,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    hinge_radius = 0.05 * WORLD_WIDTH / 2
    hinge_ball = Ball(
        x=base_x,
        y=base.top + hinge_radius,
        radius=hinge_radius,
        color="black",
        dynamic=bool(dynamic_swing_base_ball),
    )

    line_length = line_width * WORLD_WIDTH
    line = Bar(
        left=base_x - line_length / 2,
        right=base_x + line_length / 2,
        y=hinge_ball.y + hinge_ball.radius + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=True,
    )

    top_ball_radius = 0.04 * WORLD_WIDTH / 2
    green_ball = Ball(
        x=line.left + top_ball_radius,
        y=line.top + top_ball_radius,
        radius=top_ball_radius,
        color="green",
        dynamic=True,
    )
    return green_ball, hinge_ball, line, base


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    dynamic_swing_base_ball = rng.choice([0, 1])
    right_ball_size = rng.choice(np.linspace(0.04, 0.06, 4))
    dot_high = rng.choice(np.linspace(0.5, 0.7, 4))
    dot_offset = rng.choice(np.linspace(-0.2, 0.2, 4))
    line_width = rng.choice(np.linspace(0.4, 0.6, 4))
    height = rng.choice(np.linspace(0.05, 0.15, 4))
    horizontal_position = rng.choice(np.linspace(0.4, 0.6, 4))

    bar_thickness = 0.2
    green_ball, hinge_ball, line, base = _make_catapult(
        horizontal_position, height, line_width, dynamic_swing_base_ball
    )

    top_slope = Bar.from_point_and_angle(
        x=MIN_X + 0.2 * WORLD_WIDTH,
        y=MIN_Y + 0.8 * WORLD_HEIGHT,
        angle=25.0,
        length=1.4 * WORLD_WIDTH,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # set_right(line.left) for vertical bar → center_x = line.left - thickness/2.
    left_bar_length = 0.5 * WORLD_WIDTH
    left_bar = Bar(
        top=MIN_Y + left_bar_length,
        bottom=MIN_Y,
        x=line.left - bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # scale=0.9, bottom=10px≈MIN_Y, right=MAX_X.
    floor_cover = Bar(
        left=MAX_X - 0.9 * WORLD_WIDTH,
        right=MAX_X,
        y=MIN_Y + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # set_right(line.center_x + 10px≈line.x) → center_x = line.x - thickness/2.
    # bottom = line.top + 10px ≈ line.top + 0.17.
    middle_bar_length = 0.2 * WORLD_WIDTH
    middle_bar = Bar(
        top=line.top + 0.17 + middle_bar_length,
        bottom=line.top + 0.17,
        x=line.x - bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # set_right(line.right + 20px≈line.right) → center_x = line.right - thickness/2.
    right_bar_length = 0.05 * WORLD_WIDTH
    right_bar = Bar(
        top=middle_bar.top,
        bottom=middle_bar.top - right_bar_length,
        x=line.right - bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    right_ball_radius = right_ball_size * WORLD_WIDTH / 2
    blue_ball = Ball(
        x=(line.x + line.right) / 2 - right_ball_radius,
        y=line.top + right_ball_radius,
        radius=right_ball_radius,
        color="blue",
        dynamic=True,
    )

    dot_length = 0.02 * WORLD_WIDTH
    dot = Bar(
        left=line.x + line.length * dot_offset / 2,
        right=line.x + line.length * dot_offset / 2 + dot_length,
        y=MIN_Y + dot_high * WORLD_HEIGHT + dot_length / 2,
        thickness=dot_length,
        color="black",
        dynamic=False,
    )

    # scale = left_bar.left / scene.width ≈ (left_bar.x - thickness/2 - MIN_X) / W.
    purple_ground = Bar(
        left=MIN_X,
        right=left_bar.left,
        y=MIN_Y + bar_thickness / 2,
        thickness=bar_thickness,
        color="purple",
        dynamic=False,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "green_ball": green_ball,
        "blue_ball": blue_ball,
        "hinge_ball": hinge_ball,
        "line": line,
        "base": base,
        "top_slope": top_slope,
        "left_bar": left_bar,
        "floor_cover": floor_cover,
        "middle_bar": middle_bar,
        "right_bar": right_bar,
        "dot": dot,
        "purple_ground": purple_ground,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00116",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball to the purple ground."},
    )
