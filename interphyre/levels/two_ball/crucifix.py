import numpy as np
from interphyre.objects import Ball, Bar, Cross
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "purple_ground", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    base_y_options = [0.05 * i for i in range(0, 10)]
    base_x_options = [0.05 * i for i in range(0, 10)]
    scale_options = [0.35, 0.45, 0.55]

    base_y_frac = rng.choice(base_y_options)
    base_x_frac = rng.choice(base_x_options)
    scale = rng.choice(scale_options)

    bar_thickness = 0.2
    cross_thickness = 0.15
    spread = 77.5

    # Horizontal base platform.
    base_length = 0.15 * WORLD_WIDTH
    base_cx = MIN_X + (0.25 + base_x_frac) * WORLD_WIDTH
    base_bottom = MIN_Y + base_y_frac * WORLD_HEIGHT
    base = Bar(
        left=base_cx - base_length / 2,
        right=base_cx + base_length / 2,
        y=base_bottom + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Two tiny vertical posts at the ends of the base (scale=0.02, height=0.2).
    post_length = 0.02 * WORLD_WIDTH
    left_post = Bar(
        top=base.top + post_length,
        bottom=base.top,
        x=base.left + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_post = Bar(
        top=base.top + post_length,
        bottom=base.top,
        x=base.right - bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Dynamic standingstick: single Cross sitting on the base platform (body_angle=0).
    # The two bars are at ±77.5° from horizontal; the V opens upward, cradling the ball.
    arm_length = scale * WORLD_WIDTH / 3
    # max_y from body center = arm * sin(77.5°)
    cross_ext_y = arm_length * np.sin(np.radians(spread))
    sticks_body_y = base.top + cross_ext_y

    sticks = Cross(
        x=base_cx,
        y=sticks_body_y,
        angle=0.0,
        spread=spread,
        arm_length=arm_length,
        thickness=cross_thickness,
        color="gray",
        dynamic=True,
    )

    # Green ball nestled inside the upward V.
    # Cross(angle=0, spread=77.5): upper arms at ±77.5°; bisector points straight up.
    # Half-angle between upper arms = 12.5°; h = contact_dist / sin(12.5°).
    ball_radius = WORLD_WIDTH * 0.03 / 4
    contact_dist = ball_radius + cross_thickness / 2
    h_bisector = contact_dist / np.sin(np.radians(12.5))  # bisector is 90° (straight up)

    green_ball = Ball(
        x=base_cx,
        y=sticks_body_y + h_bisector,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    # Static cover bar just above the standingstick, trapping the ball inside.
    sticks_top = sticks_body_y + cross_ext_y
    top_bar_length = 0.15 * WORLD_WIDTH
    top_bar = Bar(
        left=base_cx - top_bar_length / 2,
        right=base_cx + top_bar_length / 2,
        y=sticks_top + 0.05 * WORLD_HEIGHT + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Two small flanking balls sit at the body center height, touching the base edges.
    left_ball = Ball(
        x=base.left - ball_radius,
        y=sticks_body_y,
        radius=ball_radius,
        color="gray",
        dynamic=True,
    )
    right_ball = Ball(
        x=base.right + ball_radius,
        y=sticks_body_y,
        radius=ball_radius,
        color="gray",
        dynamic=True,
    )

    purple_ground = Bar(
        left=MIN_X,
        right=MAX_X,
        y=MIN_Y + bar_thickness / 2,
        thickness=bar_thickness,
        color="purple",
        dynamic=False,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "green_ball": green_ball,
        "base": base,
        "left_post": left_post,
        "right_post": right_post,
        "sticks": sticks,
        "top_bar": top_bar,
        "left_ball": left_ball,
        "right_ball": right_ball,
        "purple_ground": purple_ground,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="crucifix",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball to the purple ground."},
    )
