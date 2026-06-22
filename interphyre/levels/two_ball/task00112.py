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

    num_bars_options = list(range(5, 9))          # [5, 6, 7, 8]
    bar_y_options = np.linspace(0.4, 0.8, 10)
    ball_x_options = np.linspace(0.1, 0.4, 10)

    bar_thickness = 0.2
    ball_radius = 0.1 * WORLD_WIDTH / 2
    left = rng.choice([True, False])

    purple_ground = Bar(
        left=MIN_X,
        right=MAX_X,
        y=MIN_Y + bar_thickness / 2,
        thickness=bar_thickness,
        color="purple",
        dynamic=False,
    )

    # Sample num_bars first; filter bar_y so ball2 fits between dominos and obstacle.
    num_bars = rng.choice(num_bars_options)
    last_bar_length = (0.15 + 0.05 * (num_bars - 1)) * WORLD_WIDTH
    last_bar_top = purple_ground.top + last_bar_length
    valid_bar_ys = [
        y for y in bar_y_options
        if MIN_Y + y * WORLD_HEIGHT - last_bar_top > 2 * ball_radius
    ]
    bar_y = rng.choice(valid_bar_ys)
    ball_x = rng.choice(ball_x_options)

    multiplier = 0.1 if left else -0.1
    offset = 0.2 if left else 0.8

    bars = []
    for idx in range(num_bars):
        bar_scale = 0.15 + 0.05 * idx
        bar_length = bar_scale * WORLD_WIDTH
        # set_left in old PHYRE → left edge at (offset + multiplier*idx)*W → center at left+thickness/2.
        bar_left = MIN_X + (offset + multiplier * idx) * WORLD_WIDTH
        bar = Bar(
            top=purple_ground.top + bar_length,
            bottom=purple_ground.top,
            x=bar_left + bar_thickness / 2,
            thickness=bar_thickness,
            color="gray",
            dynamic=True,
        )
        bars.append(bar)

    obstacle_length = 0.7 * WORLD_WIDTH
    obstacle_bottom = MIN_Y + bar_y * WORLD_HEIGHT
    if left:
        obstacle = Bar(
            left=MAX_X - obstacle_length,
            right=MAX_X,
            y=obstacle_bottom + bar_thickness / 2,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )
    else:
        obstacle = Bar(
            left=MIN_X,
            right=MIN_X + obstacle_length,
            y=obstacle_bottom + bar_thickness / 2,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )

    last_bar = bars[-1]
    ball1_x = (1.0 - ball_x if left else ball_x) * WORLD_WIDTH + MIN_X
    green_ball = Ball(
        x=ball1_x,
        y=MIN_Y + 0.9 * WORLD_HEIGHT + ball_radius,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    # Ball2 centered in gap between last domino top and obstacle bottom.
    ball2_y = last_bar.top + (obstacle.bottom - last_bar.top) / 2
    ball2_x = last_bar.left + ball_radius if left else last_bar.right - ball_radius
    gray_ball = Ball(
        x=ball2_x,
        y=ball2_y,
        radius=ball_radius,
        color="gray",
        dynamic=True,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "green_ball": green_ball,
        "gray_ball": gray_ball,
        "purple_ground": purple_ground,
        "obstacle": obstacle,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }
    for idx, bar in enumerate(bars):
        objects[f"bar_{idx}"] = bar

    return Level(
        name="task00112",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball to the purple ground."},
    )
