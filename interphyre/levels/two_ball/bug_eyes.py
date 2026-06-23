import numpy as np
from interphyre.objects import Ball, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MAX_Y, MIN_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    ball_size = 0.1
    bar_x_options = np.linspace(0.1, 0.4, 7)
    bottom_options = np.linspace(0.0, 0.5, 7)

    hole_left = rng.choice(bar_x_options)
    hole_right = rng.choice(bar_x_options)
    bottom = rng.choice(bottom_options)

    ball_radius = ball_size * WORLD_WIDTH / 2
    # Green ball placed at hole_left fraction from the left wall;
    # blue ball placed at hole_right fraction from the right wall.
    green_ball_x = MIN_X + hole_left * WORLD_WIDTH
    blue_ball_x = MIN_X + (1 - hole_right) * WORLD_WIDTH
    ball_y = MIN_Y + 0.9 * WORLD_HEIGHT + ball_radius

    green_ball = Ball(
        x=green_ball_x,
        y=ball_y,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )
    blue_ball = Ball(
        x=blue_ball_x,
        y=ball_y,
        radius=ball_radius,
        color="blue",
        dynamic=True,
    )

    bar_thickness = 0.2
    plateau_top = MIN_Y + bottom * WORLD_HEIGHT
    plateau = Bar(
        left=MIN_X,
        right=MAX_X,
        y=plateau_top - bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    vertical_bar_length = 0.1 * WORLD_WIDTH
    left_bar = Bar(
        top=plateau.top + vertical_bar_length,
        bottom=plateau.top,
        x=green_ball_x + ball_radius,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_bar = Bar(
        top=plateau.top + vertical_bar_length,
        bottom=plateau.top,
        x=blue_ball_x - ball_radius,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Separator hangs from the top between the two vertical side bars.
    # Center x matches old PHYRE: left=bar1.left + (bar2.left-bar1.left)/2
    # which equals (bar1.x + bar2.x)/2 in center-based coordinates.
    separator_length = (1.0 - bottom - 0.1) * WORLD_HEIGHT
    separator_x = (left_bar.x + right_bar.x) / 2
    separator = Bar(
        top=MAX_Y,
        bottom=MAX_Y - separator_length,
        x=separator_x,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "green_ball": green_ball,
        "blue_ball": blue_ball,
        "plateau": plateau,
        "left_bar": left_bar,
        "right_bar": right_bar,
        "separator": separator,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="bug_eyes",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
