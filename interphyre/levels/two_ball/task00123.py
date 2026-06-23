import numpy as np
from interphyre.objects import Ball, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "blue_ball", success_time)


def _create_element(cx, cy, left: bool):
    """Tilted bar structure with a ball perched on a horizontal shelf.

    The original PHYRE used a standingsticks (wide fan shape) as a cradle.
    We approximate with two tilted bars framing a horizontal shelf that
    stably supports the ball from below — ball CG is well within the shelf width.

    Returns (ball, top_bar, shelf).
    """
    bar_thickness = 0.2
    bar_length = 0.25 * WORLD_WIDTH   # = 2.5
    bar_half = bar_length / 2         # = 1.25
    cos30 = np.cos(np.radians(30.0))  # ≈ 0.866
    sin30 = np.sin(np.radians(30.0))  # = 0.5
    half_proj_x = bar_half * cos30    # ≈ 1.083
    half_proj_y = bar_half * sin30    # = 0.625
    angle = -30.0 if left else 30.0

    # Two parallel tilted bars framing the structure.
    bottom_bar = Bar.from_point_and_angle(
        x=cx, y=cy, angle=angle,
        length=bar_length, thickness=bar_thickness,
        color="black", dynamic=False,
    )
    top_bar = Bar.from_point_and_angle(
        x=cx, y=cy + 0.18 * WORLD_HEIGHT, angle=angle,
        length=bar_length, thickness=bar_thickness,
        color="black", dynamic=False,
    )

    # Horizontal shelf extending outward from the lower end of bottom_bar.
    # Wide enough (1.5) that ball radius 0.5 is stably supported with no overhang.
    shelf_length = 0.15 * WORLD_WIDTH  # = 1.5
    # Shelf sits at the approximate height of the lower end of bottom_bar.
    shelf_y = cy - half_proj_y + bar_thickness / 2
    if left:
        # Lower-right end of bottom_bar: shelf extends rightward from cx+half_proj_x.
        shelf_left = cx + half_proj_x - bar_thickness / 2
        shelf = Bar(
            left=shelf_left,
            right=shelf_left + shelf_length,
            y=shelf_y,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )
    else:
        # Lower-left end of bottom_bar: shelf extends leftward from cx-half_proj_x.
        shelf_right = cx - half_proj_x + bar_thickness / 2
        shelf = Bar(
            left=shelf_right - shelf_length,
            right=shelf_right,
            y=shelf_y,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )

    # Ball centered on shelf — CG directly above support, stable equilibrium.
    ball_radius = 0.1 * WORLD_WIDTH / 2  # = 0.5
    ball_x = (shelf.left + shelf.right) / 2
    ball_y = shelf.top + ball_radius
    ball = Ball(
        x=ball_x, y=ball_y, radius=ball_radius,
        color="green" if left else "blue",
        dynamic=True,
    )

    return ball, top_bar, shelf


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    center_x_options = np.linspace(0.3, 0.7, 10)
    center_y_options = np.linspace(0.3, 0.7, 10)

    # center2_x - center1_x > 0.35: filter center1_x to guarantee a valid center2_x.
    valid_c1x = [x for x in center_x_options if any(p - x > 0.35 for p in center_x_options)]
    c1_x_frac = rng.choice(valid_c1x)
    valid_c2x = [x for x in center_x_options if x - c1_x_frac > 0.35]
    c2_x_frac = rng.choice(valid_c2x)
    c1_y_frac = rng.choice(center_y_options)
    c2_y_frac = rng.choice(center_y_options)

    cx1 = MIN_X + c1_x_frac * WORLD_WIDTH
    cy1 = MIN_Y + c1_y_frac * WORLD_HEIGHT
    cx2 = MIN_X + c2_x_frac * WORLD_WIDTH
    cy2 = MIN_Y + c2_y_frac * WORLD_HEIGHT

    green_ball, top_bar_1, shelf_1 = _create_element(cx1, cy1, left=True)
    blue_ball, top_bar_2, shelf_2 = _create_element(cx2, cy2, left=False)

    bar_thickness = 0.2
    bar_half_proj = (0.25 * WORLD_WIDTH / 2) * np.cos(np.radians(30.0))  # ≈ 1.083
    top_bar_top = 0.625  # (bar_half * sin30) for bars 0.18*H above cy

    # Obstacle bars above each top_bar to block simple solutions.
    # scale=0.3 → length=3.0; bottom=top.top+0.1*H; right=top.left (left) or left=top.right (right).
    obs_length = 0.3 * WORLD_WIDTH  # = 3.0
    obs1_top_y = cy1 + 0.18 * WORLD_HEIGHT + top_bar_top + 0.1 * WORLD_HEIGHT
    obs1 = Bar(
        left=cx1 - bar_half_proj - obs_length,
        right=cx1 - bar_half_proj,
        y=obs1_top_y + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    obs2_top_y = cy2 + 0.18 * WORLD_HEIGHT + top_bar_top + 0.1 * WORLD_HEIGHT
    obs2 = Bar(
        left=cx2 + bar_half_proj,
        right=cx2 + bar_half_proj + obs_length,
        y=obs2_top_y + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Flat floor — no convergent ramps, so balls that fall off shelves don't
    # naturally roll into each other. A player push is required to bring them together.
    floor = Bar(
        left=MIN_X,
        right=MAX_X,
        y=MIN_Y + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "green_ball": green_ball,
        "blue_ball": blue_ball,
        "top_bar_1": top_bar_1,
        "top_bar_2": top_bar_2,
        "shelf_1": shelf_1,
        "shelf_2": shelf_2,
        "obstacle_1": obs1,
        "obstacle_2": obs2,
        "floor": floor,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00123",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball touch the blue ball."},
    )
