import numpy as np
from interphyre.objects import Ball, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "purple_ground", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    # Old PHYRE: base_y = [0.05*i for i in range(0,10)], base_x = same, scale = [0.35,0.45,0.55]
    base_y_options = [0.05 * i for i in range(0, 10)]  # 0.0..0.45
    base_x_options = [0.05 * i for i in range(0, 10)]  # 0.0..0.45
    scale_options = [0.35, 0.45, 0.55]

    base_y_frac = rng.choice(base_y_options)
    base_x_frac = rng.choice(base_x_options)
    scale = rng.choice(scale_options)

    bar_thickness = 0.2

    # Horizontal base platform: center_x=(0.25+base_x)*W, bottom=base_y*H, length=0.15*W.
    base_length = 0.15 * WORLD_WIDTH  # = 1.5
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

    # Tiny upright posts at each end of base (scale=0.02, angle=90, length=0.2).
    post_length = 0.02 * WORLD_WIDTH  # = 0.2
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

    # Dynamic standingsticks approximated as two symmetric diverging bars.
    sticks_length = scale * WORLD_WIDTH
    sticks_bottom = base.top
    sticks_top = sticks_bottom + sticks_length
    sticks_mid_y = (sticks_bottom + sticks_top) / 2
    left_stick = Bar.from_point_and_angle(
        x=base_cx - 0.05 * WORLD_WIDTH,
        y=sticks_mid_y,
        angle=25.0,
        length=sticks_length,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )
    right_stick = Bar.from_point_and_angle(
        x=base_cx + 0.05 * WORLD_WIDTH,
        y=sticks_mid_y,
        angle=-25.0,
        length=sticks_length,
        thickness=bar_thickness,
        color="gray",
        dynamic=True,
    )

    # Small ball hovering at sticks top: set_top(sticks.top - 0.005*H), center_x=base_cx.
    ball_radius = 0.03 * WORLD_WIDTH / 2  # = 0.15
    green_ball = Ball(
        x=base_cx,
        y=sticks_top - 0.005 * WORLD_HEIGHT - ball_radius,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    # Cover bar just above sticks: center_x=green_ball.x, bottom=sticks_top+0.05*H.
    top_bar_length = 0.15 * WORLD_WIDTH  # = 1.5
    top_bar = Bar(
        left=green_ball.x - top_bar_length / 2,
        right=green_ball.x + top_bar_length / 2,
        y=sticks_top + 0.05 * WORLD_HEIGHT + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Two flanking balls beside the base: right=base.left and left=base.right.
    left_ball = Ball(
        x=base.left - ball_radius,
        y=sticks_mid_y,
        radius=ball_radius,
        color="gray",
        dynamic=True,
    )
    right_ball = Ball(
        x=base.right + ball_radius,
        y=sticks_mid_y,
        radius=ball_radius,
        color="gray",
        dynamic=True,
    )

    # Full-width floor (purple for success condition).
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
        "left_stick": left_stick,
        "right_stick": right_stick,
        "top_bar": top_bar,
        "left_ball": left_ball,
        "right_ball": right_ball,
        "purple_ground": purple_ground,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00124",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball to the purple ground."},
    )
