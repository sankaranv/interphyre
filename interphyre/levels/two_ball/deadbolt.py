import numpy as np
from interphyre.objects import Ball, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_ground", success_time
    )


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    ball_sizes = [0.1, 0.15, 0.2]
    hole_sizes = [0.11, 0.16, 0.21]
    hole_lefts = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    bar_heights = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    bar_thickness = 0.2

    green_ball_x = 0.0
    ball_top = MIN_Y + 0.95 * WORLD_HEIGHT

    # Ball must fit through the hole; hole must stay within scene bounds.
    hole_size = rng.choice(hole_sizes)
    valid_ball_sizes = [b for b in ball_sizes if b <= hole_size]
    ball_size = rng.choice(valid_ball_sizes)
    ball_radius = ball_size * WORLD_WIDTH / 2

    # Hole must not be entirely under the ball (ball at x=0 occupies ±ball_radius).
    valid_hole_lefts = [
        h for h in hole_lefts
        if h + hole_size < 1.0
        and not (h <= 0.5 - ball_size / 2 and h + hole_size >= 0.5 + ball_size / 2)
    ]
    hole_left = rng.choice(valid_hole_lefts)
    hole_right = hole_left + hole_size

    # Bottom bar must sit high enough that the ball fits under it from the floor.
    # Condition: bottom_bar_height > ball_size / 2, combined with bottom_bar_height > 0
    # gives bar_height > 2.5 * ball_size.
    valid_bar_heights = [h for h in bar_heights if h > 2.5 * ball_size]
    bar_height = rng.choice(valid_bar_heights)
    bottom_bar_height = bar_height - 2 * ball_size

    green_ball_y = ball_top - ball_radius
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    top_bar_y = MIN_Y + bar_height * WORLD_HEIGHT + bar_thickness / 2
    hole_left_x = MIN_X + hole_left * WORLD_WIDTH
    hole_right_x = MIN_X + hole_right * WORLD_WIDTH

    left_top_bar = Bar(
        left=MIN_X,
        right=hole_left_x,
        y=top_bar_y,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_top_bar = Bar(
        left=hole_right_x,
        right=MAX_X,
        y=top_bar_y,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    shift = 0.15 if hole_left < 0.5 else -0.15
    bottom_bar_y = MIN_Y + bottom_bar_height * WORLD_HEIGHT + bar_thickness / 2
    bottom_hole_left = hole_left + shift
    bottom_hole_right = bottom_hole_left + hole_size
    bottom_hole_left_x = MIN_X + bottom_hole_left * WORLD_WIDTH
    bottom_hole_right_x = MIN_X + bottom_hole_right * WORLD_WIDTH

    left_bottom_bar = Bar(
        left=MIN_X,
        right=bottom_hole_left_x,
        y=bottom_bar_y,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_bottom_bar = Bar(
        left=bottom_hole_right_x,
        right=MAX_X,
        y=bottom_bar_y,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Small vertical lips at the hole edges of the bottom bar to guide the ball.
    # Each lip's inner face aligns with the hole edge (bar center offset by thickness/2).
    obstacle_height = 0.02 * WORLD_HEIGHT
    left_obstacle = Bar(
        top=left_bottom_bar.top + obstacle_height,
        bottom=left_bottom_bar.top,
        x=left_bottom_bar.right - bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_obstacle = Bar(
        top=right_bottom_bar.top + obstacle_height,
        bottom=right_bottom_bar.top,
        x=right_bottom_bar.left + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
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
        "left_top_bar": left_top_bar,
        "right_top_bar": right_top_bar,
        "left_bottom_bar": left_bottom_bar,
        "right_bottom_bar": right_bottom_bar,
        "left_obstacle": left_obstacle,
        "right_obstacle": right_obstacle,
        "purple_ground": purple_ground,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="deadbolt",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Drop the green ball through the holes."},
    )
