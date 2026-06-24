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
    rng = np.random.default_rng(seed)

    wall_heights = np.linspace(0.3, 0.6, 4)    # [0.3, 0.4, 0.5, 0.6]
    ramp_centers = np.linspace(0.2, 0.6, 5)    # [0.2, 0.3, 0.4, 0.5, 0.6]
    ramp_heights = np.linspace(0.6, 0.8, 3)    # [0.6, 0.7, 0.8]
    bar_angles = np.linspace(15.0, 30.0, 3)    # [15, 22.5, 30]
    ball_sizes = np.linspace(0.05, 0.1, 2)     # [0.05, 0.1]

    bar_thickness = 0.2
    ramp_length = 0.3 * WORLD_WIDTH

    ramp_center = rng.choice(ramp_centers)
    ramp_height = rng.choice(ramp_heights)
    bar_angle = rng.choice(bar_angles)
    ball_size = rng.choice(ball_sizes)

    # ramp1: tilted -20°, center_x at ramp_center, bottom at ramp_height fraction.
    ramp1_center_x = MIN_X + ramp_center * WORLD_WIDTH
    ramp1_bottom_y = MIN_Y + ramp_height * WORLD_HEIGHT
    ramp1_center_y = ramp1_bottom_y + (ramp_length / 2) * abs(np.sin(np.radians(20.0))) + bar_thickness / 2
    ramp1 = Bar.from_point_and_angle(
        x=ramp1_center_x,
        y=ramp1_center_y,
        length=ramp_length,
        angle=-20.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # ramp2: tilted at bar_angle, right end at ramp1.right + 0.15*W, top at ramp1.bottom - 0.1*H.
    ramp2_right_x = ramp1.right + 0.15 * WORLD_WIDTH
    ramp2_top_y = ramp1.bottom - 0.1 * WORLD_HEIGHT
    ramp2_center_x = ramp2_right_x - (ramp_length / 2) * np.cos(np.radians(bar_angle)) - bar_thickness / 2
    ramp2_center_y = ramp2_top_y - (ramp_length / 2) * np.sin(np.radians(bar_angle)) - bar_thickness / 2
    ramp2 = Bar.from_point_and_angle(
        x=ramp2_center_x,
        y=ramp2_center_y,
        length=ramp_length,
        angle=bar_angle,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Ball: left edge at ramp1.left, bottom at ramp1.top.
    ball_radius = ball_size * WORLD_WIDTH / 2
    green_ball = Ball(
        x=ramp1.left + ball_radius,
        y=ramp1.top + ball_radius,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    # Wall: vertical bar, center at ramp2.left - 0.15*W, bottom at floor.
    # wall_height (fraction) gives length = wall_height * WORLD_WIDTH.
    # Constraint 1: wall.left_frac >= wall_height (wall is right enough relative to its height).
    # Constraint 2: ramp2.bottom_frac - wall_height >= ball_size_frac (ball clears wall).
    wall_x = ramp2.left - 0.15 * WORLD_WIDTH
    ramp2_bottom_frac = (ramp2.bottom - MIN_Y) / WORLD_HEIGHT
    ball_size_frac = ball_size

    valid_wall_heights = [
        wh for wh in wall_heights
        if (wall_x - bar_thickness / 2 - MIN_X) / WORLD_WIDTH >= wh
        and ramp2_bottom_frac - wh >= ball_size_frac
    ]
    if not valid_wall_heights:
        valid_wall_heights = [wall_heights[0]]
    wall_height = rng.choice(valid_wall_heights)
    wall_world_length = wall_height * WORLD_WIDTH

    wall = Bar(
        top=MIN_Y + wall_world_length,
        bottom=MIN_Y,
        x=wall_x,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Goal (purple ground): horizontal bar from wall.right to right edge, at floor.
    purple_ground = Bar(
        left=wall.right,
        right=MAX_X,
        y=MIN_Y + bar_thickness / 2,
        thickness=bar_thickness,
        color="purple",
        dynamic=False,
    )

    # Slope: long bar at -20°, left end at ramp2.right + 0.05*W, top at ramp2.top.
    slope_length = 1.0 * WORLD_WIDTH
    slope_left_x = ramp2.right + 0.05 * WORLD_WIDTH
    slope_top_y = ramp2.top
    slope_center_x = slope_left_x + slope_length / 2
    slope_center_y = slope_top_y - (slope_length / 2) * abs(np.sin(np.radians(20.0))) - bar_thickness / 2
    slope = Bar.from_point_and_angle(
        x=slope_center_x,
        y=slope_center_y,
        length=slope_length,
        angle=-20.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "green_ball": green_ball,
        "ramp1": ramp1,
        "ramp2": ramp2,
        "wall": wall,
        "purple_ground": purple_ground,
        "slope": slope,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="the_relay",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball onto the purple ground."},
    )
