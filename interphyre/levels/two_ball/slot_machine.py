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

    bar_thickness = 0.2
    ball_radius = 0.07 * WORLD_WIDTH / 2
    green_ball_x = MIN_X + rng.uniform(0.2, 0.8) * WORLD_WIDTH
    green_ball_y = MIN_Y + 0.93 * WORLD_HEIGHT
    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )
    objects = {"green_ball": green_ball}

    # Bars placed below the ball; uppermost limit is two ball-heights below ball center.
    bar_count = rng.integers(6, 9)
    top_frac = (green_ball_y - ball_radius - 2 * ball_radius * 2 - MIN_Y) / WORLD_HEIGHT
    cap_length = 0.05 * WORLD_WIDTH  # bracket arm height

    for i in range(bar_count):
        bar_x = green_ball_x if i == 0 else MIN_X + rng.uniform(0.1, 0.9) * WORLD_WIDTH
        bar_length = rng.uniform(0.15, 0.35) * WORLD_WIDTH
        bar_y = MIN_Y + rng.uniform(0.05, top_frac) * WORLD_HEIGHT
        bar = Bar(
            left=bar_x - bar_length / 2,
            right=bar_x + bar_length / 2,
            y=bar_y,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )
        objects[f"bar_{i}"] = bar

        # Small caps at bar edges with probability 0.8, preventing balls from sliding off cleanly.
        if rng.uniform() < 0.8:
            objects[f"bar_{i}_right_cap"] = Bar(
                top=bar.top + cap_length,
                bottom=bar.top,
                x=bar.right - bar_thickness / 2,
                thickness=bar_thickness,
                color="black",
                dynamic=False,
            )
        if rng.uniform() < 0.8:
            objects[f"bar_{i}_left_cap"] = Bar(
                top=bar.top + cap_length,
                bottom=bar.top,
                x=bar.left + bar_thickness / 2,
                thickness=bar_thickness,
                color="black",
                dynamic=False,
            )

    # Angled trap bars at floor corners funnel ball to central purple ground.
    trap_length = 0.15 * WORLD_WIDTH
    left_trap = Bar.from_point_and_angle(
        x=MIN_X + trap_length / 2,
        y=MIN_Y + bar_thickness / 2,
        length=trap_length,
        angle=10.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    right_trap = Bar.from_point_and_angle(
        x=MAX_X - trap_length / 2,
        y=MIN_Y + bar_thickness / 2,
        length=trap_length,
        angle=-10.0,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    purple_ground = Bar(
        left=left_trap.right,
        right=right_trap.left,
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
        name="slot_machine",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Get the green ball to the purple ground."},
    )
