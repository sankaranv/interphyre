import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_ground", success_time
    )


def _make_catapult(
    horizontal_position,
    height,
    line_width,
    dynamic_swing_base_ball,
    bar_thickness,
):
    base_length = 0.1 * (10.0)
    base_x = (-5.0) + horizontal_position * (10.0)
    base_bottom = (-5.0) + height * (10.0)
    base = Bar(
        top=base_bottom + base_length,
        bottom=base_bottom,
        x=base_x,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    hinge_radius = 0.05 * (10.0) / 2
    hinge_ball = Ball(
        x=base_x,
        y=base.top + hinge_radius,
        radius=hinge_radius,
        color="black",
        dynamic=bool(dynamic_swing_base_ball),
    )

    line_length = line_width * (10.0)
    line = Bar.from_point_and_angle(
        x=base_x,
        y=hinge_ball.y + hinge_ball.radius + bar_thickness / 2,
        length=line_length,
        angle=0.0,
        thickness=bar_thickness,
        color="black",
        dynamic=True,
    )

    top_ball_radius = 0.04 * (10.0) / 2
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
    rng = np.random.default_rng(seed)

    dynamic_swing_base_ball = rng.choice([0, 1])
    right_ball_size = rng.choice(np.linspace(0.04, 0.06, 4))
    dot_high = rng.choice(np.linspace(0.5, 0.7, 4))
    dot_offset = rng.choice(np.linspace(-0.2, 0.2, 4))
    line_width = rng.choice(np.linspace(0.4, 0.6, 4))
    height = rng.choice(np.linspace(0.05, 0.15, 4))
    horizontal_position = rng.choice(np.linspace(0.4, 0.6, 4))

    bar_thickness = 0.2
    green_ball, hinge_ball, line, base = _make_catapult(
        horizontal_position,
        height,
        line_width,
        dynamic_swing_base_ball,
        bar_thickness,
    )

    top_slope = Bar.from_point_and_angle(
        x=(-5.0) + 0.2 * (10.0),
        y=(-5.0) + 0.8 * (10.0),
        angle=25.0,
        length=1.4 * (10.0),
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    left_bar_length = 0.5 * (10.0)
    left_bar = Bar(
        top=(-5.0) + left_bar_length,
        bottom=(-5.0),
        x=line.left,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    floor_cover = Bar(
        left=(5.0) - 0.9 * (10.0),
        right=(5.0),
        y=(-5.0) + 0.2 * (10.0) + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    middle_bar_length = 0.2 * (10.0)
    middle_bar_bottom = line.top + 0.1 * (10.0)
    middle_bar = Bar(
        top=middle_bar_bottom + middle_bar_length,
        bottom=middle_bar_bottom,
        x=line.x + 0.1 * (10.0),
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    right_bar_length = 0.05 * (10.0)
    right_bar = Bar(
        top=middle_bar.top,
        bottom=middle_bar.top - right_bar_length,
        x=line.right + 0.2 * (10.0),
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    right_ball_radius = right_ball_size * (10.0) / 2
    blue_ball = Ball(
        x=(line.x + line.right) / 2 - right_ball_radius,
        y=line.top + right_ball_radius,
        radius=right_ball_radius,
        color="blue",
        dynamic=True,
    )

    dot_length = 0.02 * (10.0)
    dot = Bar(
        left=line.x + line.length * dot_offset / 2,
        right=line.x + line.length * dot_offset / 2 + dot_length,
        y=(-5.0) + dot_high * (10.0) + dot_length / 2,
        thickness=dot_length,
        color="black",
        dynamic=False,
    )

    purple_ground = Bar(
        left=(-5.0),
        right=left_bar.left,
        y=(-5.0) + bar_thickness / 2,
        thickness=bar_thickness,
        color="purple",
        dynamic=False,
    )

    red_ball_1 = Ball(
        x=-3.0,
        y=4.0,
        radius=0.5,
        color="red",
        dynamic=True,
    )
    red_ball_2 = Ball(
        x=3.0,
        y=4.0,
        radius=0.5,
        color="red",
        dynamic=True,
    )

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
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball to the purple ground."},
    )
