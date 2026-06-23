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
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    bar_thickness = 0.2
    ball_radius = 0.07 * WORLD_WIDTH / 2  # scale=0.07

    ball_x = MIN_X + rng.uniform(0.2, 0.8) * WORLD_WIDTH
    ball_y = MIN_Y + 0.93 * WORLD_HEIGHT  # center of ball, not top
    green_ball = Ball(x=ball_x, y=ball_y, radius=ball_radius, color="green", dynamic=True)

    # Y range for staggered bars: from 15% height to just below ball.
    ball_bottom = ball_y - ball_radius
    top_frac = (ball_bottom - 3 * ball_radius - MIN_Y) / WORLD_HEIGHT
    bar_count = rng.integers(6, 9)  # 6, 7, or 8 bars (old PHYRE randint(6,9))
    y_fracs = np.linspace(0.15, top_frac, bar_count)

    cap_size = 0.01 * WORLD_WIDTH  # tiny horizontal end-stops (old PHYRE scale=0.01)

    objects = {"green_ball": green_ball}

    # Frontier queue: next bar's center_x comes from edges of previous bar.
    frontier = []
    for idx, y_frac in enumerate(reversed(y_fracs)):
        if rng.uniform() < 0.2:
            continue

        bar_length = rng.uniform(0.15, 0.35) * WORLD_WIDTH
        center_x = frontier.pop(0) if frontier else ball_x
        bar_y = MIN_Y + (y_frac + rng.normal() * 0.02) * WORLD_HEIGHT

        bar = Bar(
            left=center_x - bar_length / 2,
            right=center_x + bar_length / 2,
            y=bar_y,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )
        # Tiny horizontal end-stops at each edge, sitting just above bar top.
        left_cap = Bar(
            left=bar.left,
            right=bar.left + cap_size,
            y=bar.top + cap_size / 2,
            thickness=cap_size,
            color="black",
            dynamic=False,
        )
        right_cap = Bar(
            left=bar.right - cap_size,
            right=bar.right,
            y=bar.top + cap_size / 2,
            thickness=cap_size,
            color="black",
            dynamic=False,
        )

        if rng.uniform() < 0.5:
            frontier.extend([bar.left, bar.right])
        else:
            frontier.extend([bar.right, bar.left])

        objects[f"bar_{idx}"] = bar
        objects[f"left_cap_{idx}"] = left_cap
        objects[f"right_cap_{idx}"] = right_cap

    # V-shaped floor funneling ball to purple ground in the middle.
    trap_length = 0.15 * WORLD_WIDTH
    half_proj = (trap_length / 2) * np.cos(np.radians(10.0))
    trap_rise = (trap_length / 2) * np.sin(np.radians(10.0))
    left_trap = Bar.from_point_and_angle(
        x=MIN_X + half_proj,
        y=MIN_Y + trap_rise,
        angle=10.0,
        length=trap_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_trap = Bar.from_point_and_angle(
        x=MAX_X - half_proj,
        y=MIN_Y + trap_rise,
        angle=-10.0,
        length=trap_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    ground_length = right_trap.left - left_trap.right
    purple_ground = Bar(
        left=left_trap.right,
        right=left_trap.right + ground_length,
        y=MIN_Y + bar_thickness / 2,
        thickness=bar_thickness,
        color="purple",
        dynamic=False,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects.update({
        "left_trap": left_trap,
        "right_trap": right_trap,
        "purple_ground": purple_ground,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    })

    return Level(
        name="fire_escape",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball to the purple ground."},
    )
