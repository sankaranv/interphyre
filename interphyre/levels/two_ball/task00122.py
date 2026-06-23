import numpy as np
from interphyre.objects import Ball, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("falling_sticks", "purple_ground", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    scale_options = np.linspace(0.5, 0.7, 4)
    scale2_options = np.linspace(0.4, 0.6, 4)
    center_x_options = np.linspace(0.25, 0.75, 5)
    height_options = np.linspace(0.0, 0.075, 2)

    scale = rng.choice(scale_options)
    scale2 = rng.choice(scale2_options)
    center_x = rng.choice(center_x_options)
    height = rng.choice(height_options)

    bar_thickness = 0.2
    # Purple ground: full-width, bottom at height*H above MIN_Y.
    purple_ground = Bar(
        left=MIN_X,
        right=MAX_X,
        y=MIN_Y + height * WORLD_HEIGHT + bar_thickness / 2,
        thickness=bar_thickness,
        color="purple",
        dynamic=False,
    )

    # Two static upright posts flanking center_x, spaced post_gap apart.
    # The dynamic bar rests horizontally across both posts (like a table top) —
    # two-point support is inherently stable in Box2D.  Player knocks the bar off.
    post_height = scale * WORLD_WIDTH
    post_gap = 0.25 * WORLD_WIDTH  # = 2.5 — wide enough that bar spans both clearly
    base_cx = MIN_X + center_x * WORLD_WIDTH
    left_post = Bar(
        bottom=purple_ground.top,
        top=purple_ground.top + post_height,
        x=base_cx - post_gap / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_post = Bar(
        bottom=purple_ground.top,
        top=purple_ground.top + post_height,
        x=base_cx + post_gap / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Falling bar rests horizontally across the two post tops.
    # Its length = scale2 * WORLD_WIDTH; centered between the posts.
    falling_length = scale2 * WORLD_WIDTH
    falling_sticks = Bar(
        left=base_cx - falling_length / 2,
        right=base_cx + falling_length / 2,
        y=left_post.top + bar_thickness / 2,
        thickness=bar_thickness,
        color="green",
        dynamic=True,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "left_post": left_post,
        "right_post": right_post,
        "falling_sticks": falling_sticks,
        "purple_ground": purple_ground,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00122",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the falling sticks touch the ground."},
    )
