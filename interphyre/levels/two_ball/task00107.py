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


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    obstacle_widths = [val * 0.1 for val in range(1, 8)]   # [0.1, ..., 0.7]
    obstacle_ys = [val * 0.1 for val in range(4, 8)]        # [0.4, 0.5, 0.6, 0.7]
    obstacle_xs = [val * 0.1 for val in range(0, 11)]       # [0.0, 0.1, ..., 1.0]
    bar_thickness = 0.2

    # Upper obstacle must fit within scene bounds.
    obstacle_width = rng.choice(obstacle_widths)
    valid_xs = [x for x in obstacle_xs if x + obstacle_width <= 1.0]
    obstacle_x = rng.choice(valid_xs)
    obstacle_y = rng.choice(obstacle_ys)

    # Upper obstacle bar.
    upper_left = MIN_X + obstacle_x * WORLD_WIDTH
    upper_right = MIN_X + (obstacle_x + obstacle_width) * WORLD_WIDTH
    upper_bar = Bar(
        left=upper_left,
        right=upper_right,
        y=MIN_Y + obstacle_y * WORLD_HEIGHT + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Lower bar with hole at same horizontal position as upper bar, 0.2 lower.
    lower_y = MIN_Y + (obstacle_y - 0.2) * WORLD_HEIGHT + bar_thickness / 2
    objects = {"upper_bar": upper_bar}

    if obstacle_x > 0.0:
        left_lower = Bar(
            left=MIN_X,
            right=upper_left,
            y=lower_y,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )
        objects["left_lower"] = left_lower
        # Blocker at hole edge: right edge of left_lower bar.
        objects["left_blocker"] = Bar(
            top=left_lower.top + 0.02 * WORLD_HEIGHT,
            bottom=left_lower.top,
            x=left_lower.right - bar_thickness / 2,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )

    right_scale = 1.0 - obstacle_x - obstacle_width
    if right_scale > 0.0:
        right_lower = Bar(
            left=upper_right,
            right=MAX_X,
            y=lower_y,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )
        objects["right_lower"] = right_lower
        # Blocker at hole edge: left edge of right_lower bar.
        objects["right_blocker"] = Bar(
            top=right_lower.top + 0.02 * WORLD_HEIGHT,
            bottom=right_lower.top,
            x=right_lower.left + bar_thickness / 2,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )

    ball_radius = 0.1 * WORLD_WIDTH / 2
    green_ball = Ball(
        x=MIN_X + (obstacle_x + obstacle_width / 2) * WORLD_WIDTH,
        y=MIN_Y + 0.9 * WORLD_HEIGHT + ball_radius,
        radius=ball_radius,
        color="green",
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

    objects["green_ball"] = green_ball
    objects["purple_ground"] = purple_ground
    objects["red_ball_1"] = red_ball_1
    objects["red_ball_2"] = red_ball_2

    return Level(
        name="task00107",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball to the purple ground."},
    )
