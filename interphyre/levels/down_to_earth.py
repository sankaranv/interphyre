import numpy as np
from dataclasses import dataclass
from typing import cast

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Bar, PhyreObject


@dataclass
class DownToEarthParams:
    """Override parameters for down_to_earth level generation.

    All fields default to None, meaning the value is drawn from the RNG as usual.
    Setting a field fixes that variable while leaving all others RNG-determined.

    Critical invariant: the level builder always draws from the RNG in the same
    fixed order regardless of which overrides are set, so that overriding one
    variable does not shift the RNG state and alter downstream draws.
    """

    platform_x: float | None = None
    platform_width: float | None = None
    platform_y: float | None = None
    red_ball_radius: float | None = None


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration(
        "green_ball", "purple_ground", success_time
    )


@register_level
def build_level(seed=None, params: DownToEarthParams | None = None) -> Level:
    rng = np.random.default_rng(seed)
    p = params or DownToEarthParams()

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
    platform_width = p.platform_width if p.platform_width is not None else platform_width_draw
    platform_x = p.platform_x if p.platform_x is not None else platform_x_draw
    platform_y = p.platform_y if p.platform_y is not None else platform_y_draw
    red_ball_radius = p.red_ball_radius if p.red_ball_radius is not None else red_ball_radius_draw

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
