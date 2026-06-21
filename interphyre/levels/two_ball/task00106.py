import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, InterphyreObject
from interphyre.level import Level
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


def _make_catapult(x_frac: float, y_frac: float, left: bool):
    bar_thickness = 0.2
    base_length = 0.1 * (10.0)
    base_x = (-5.0) + x_frac * (10.0)
    base_y = (-5.0) + y_frac * (10.0) + bar_thickness / 2
    base = Bar.from_point_and_angle(
        x=base_x,
        y=base_y,
        length=base_length,
        angle=0.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    support_length = 0.02 * (10.0)
    left_support = Bar(
        top=base.top + support_length,
        bottom=base.top,
        x=base.left,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_support = Bar(
        top=base.top + support_length,
        bottom=base.top,
        x=base.right,
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
        dynamic=False,
    )

    line_length = 0.25 * (10.0)
    line_angle = 20.0 if left else -20.0
    line_y = hinge_ball.y + hinge_ball.radius + bar_thickness / 2
    line = Bar.from_point_and_angle(
        x=base_x,
        y=line_y,
        length=line_length,
        angle=line_angle,
        thickness=bar_thickness,
        color="black",
        dynamic=True,
    )

    top_ball_radius = 0.07 * (10.0) / 2
    line_top = line.y + (line.length / 2) * np.sin(np.radians(line.angle)) + bar_thickness / 2
    if left:
        top_ball_x = line.left + top_ball_radius
    else:
        top_ball_x = line.right - top_ball_radius
    top_ball = Ball(
        x=top_ball_x,
        y=line_top + top_ball_radius,
        radius=top_ball_radius,
        color="green" if left else "blue",
        dynamic=True,
    )

    return top_ball, base, left_support, right_support, hinge_ball, line


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    catapult_xs = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    catapult_ys = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]

    while True:
        catapult1_x = rng.choice(catapult_xs)
        catapult2_x = rng.choice(catapult_xs)
        if catapult1_x + 0.3 < catapult2_x:
            break
    catapult1_y = rng.choice(catapult_ys)
    catapult2_y = rng.choice(catapult_ys)

    (
        green_ball,
        base_1,
        left_support_1,
        right_support_1,
        hinge_ball_1,
        line_1,
    ) = _make_catapult(catapult1_x, catapult1_y, left=True)
    (
        blue_ball,
        base_2,
        left_support_2,
        right_support_2,
        hinge_ball_2,
        line_2,
    ) = _make_catapult(catapult2_x, catapult2_y, left=False)

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
        "base_1": base_1,
        "base_2": base_2,
        "left_support_1": left_support_1,
        "right_support_1": right_support_1,
        "left_support_2": left_support_2,
        "right_support_2": right_support_2,
        "hinge_ball_1": hinge_ball_1,
        "hinge_ball_2": hinge_ball_2,
        "line_1": line_1,
        "line_2": line_2,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00106",
        objects=cast(dict[str, InterphyreObject], objects),
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
