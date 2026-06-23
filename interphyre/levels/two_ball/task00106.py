import numpy as np
from interphyre.objects import Ball, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


def _make_catapult(x_frac: float, y_frac: float, left: bool, ball_color: str) -> dict:
    bar_thickness = 0.2
    base_length = 0.1 * WORLD_WIDTH
    base_x = MIN_X + x_frac * WORLD_WIDTH
    base_y = MIN_Y + y_frac * WORLD_HEIGHT + bar_thickness / 2
    base = Bar(
        x=base_x,
        y=base_y,
        length=base_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    support_height = 0.02 * WORLD_WIDTH
    left_support = Bar(
        top=base.top + support_height,
        bottom=base.top,
        x=base.left + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_support = Bar(
        top=base.top + support_height,
        bottom=base.top,
        x=base.right - bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    hinge_radius = 0.05 * WORLD_WIDTH / 2
    hinge = Ball(
        x=base_x,
        y=base.top + hinge_radius,
        radius=hinge_radius,
        color="black",
        dynamic=False,
    )

    line_length = 0.25 * WORLD_WIDTH
    line_angle = 20.0 if left else -20.0
    line = Bar.from_point_and_angle(
        x=base_x,
        y=hinge.y + hinge.radius + bar_thickness / 2,
        length=line_length,
        angle=line_angle,
        thickness=bar_thickness,
        color="black",
        dynamic=True,
    )

    top_ball_radius = 0.07 * WORLD_WIDTH / 2
    # Ball sits at line.top; positioned at line.left (left catapult) or line.right (right).
    if left:
        top_ball_x = line.left + top_ball_radius
    else:
        top_ball_x = line.right - top_ball_radius
    top_ball = Ball(
        x=top_ball_x,
        y=line.top + top_ball_radius,
        radius=top_ball_radius,
        color=ball_color,
        dynamic=True,
    )

    return {
        "top_ball": top_ball,
        "base": base,
        "left_support": left_support,
        "right_support": right_support,
        "hinge": hinge,
        "line": line,
    }


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    catapult_xs = [0.1 * val for val in range(2, 9)]  # [0.2, ..., 0.8]
    catapult_ys = [0.1 * val for val in range(0, 7)]  # [0.0, ..., 0.6]

    # Second catapult must be at least 0.3 to the right of the first.
    valid_c1_x = [x for x in catapult_xs if x + 0.3 < catapult_xs[-1]]
    catapult1_x = rng.choice(valid_c1_x)
    valid_c2_x = [x for x in catapult_xs if x > catapult1_x + 0.3]
    catapult2_x = rng.choice(valid_c2_x)

    catapult1_y = rng.choice(catapult_ys)
    catapult2_y = rng.choice(catapult_ys)

    c1 = _make_catapult(catapult1_x, catapult1_y, left=True, ball_color="green")
    c2 = _make_catapult(catapult2_x, catapult2_y, left=False, ball_color="blue")

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "green_ball": c1["top_ball"],
        "blue_ball": c2["top_ball"],
        "base_1": c1["base"],
        "left_support_1": c1["left_support"],
        "right_support_1": c1["right_support"],
        "hinge_1": c1["hinge"],
        "line_1": c1["line"],
        "base_2": c2["base"],
        "left_support_2": c2["left_support"],
        "right_support_2": c2["right_support"],
        "hinge_2": c2["hinge"],
        "line_2": c2["line"],
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00106",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
