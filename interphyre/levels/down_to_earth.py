import numpy as np
from typing import cast

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Bar, PhyreObject


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_ground", success_time
    )


@register_level
def build_level(seed=None, **overrides) -> Level:
    rng = np.random.default_rng(seed)

    # Ground plane
    purple_ground = Bar(
        left=-5,
        right=5,
        y=-4.9,
        thickness=0.2,
        color="purple",
        dynamic=False,
    )

    # Always draw all RNG values in fixed order before applying any overrides.
    # This preserves the draw sequence so that overriding one variable does not
    # shift downstream draws — e.g. platform_x_draw still uses platform_width_draw
    # (the drawn value) rather than the overridden platform_width.
    platform_width_draw = rng.uniform(1, 7)
    platform_x_draw = rng.uniform(-5, 5 - platform_width_draw)
    platform_y_draw = rng.uniform(-2, 2)
    red_ball_radius_draw = rng.uniform(0.3, 0.6)

    # Apply overrides after all draws
    platform_width = overrides.get("platform_width", platform_width_draw)
    platform_x = overrides.get("platform_x", platform_x_draw)
    platform_y = overrides.get("platform_y", platform_y_draw)
    red_ball_radius = overrides.get("red_ball_radius", red_ball_radius_draw)

    # Platform
    platform = Bar(
        left=platform_x,
        right=platform_x + platform_width,
        y=platform_y,
        thickness=0.2,
        color="black",
        dynamic=False,
    )

    # Green ball centered above platform, near the top of the screen
    green_ball_radius = 0.5
    green_ball_x = platform_x + platform_width / 2
    green_ball_y = 4.5 - green_ball_radius

    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    # Red action ball
    red_ball = Ball(
        x=0,
        y=0,
        radius=red_ball_radius,
        color="red",
        dynamic=True,
    )

    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "purple_ground": purple_ground,
        "platform": platform,
    }

    return Level(
        name="down_to_earth",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={"description": "Make the green ball hit the ground"},
    )
