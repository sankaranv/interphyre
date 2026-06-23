import numpy as np
from interphyre.objects import Ball, Bar, Cross
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("falling_sticks", "purple_ground", success_time)


def _cross_extents(arm_length, body_angle_deg, spread_deg):
    """Bounding-box half-extents (max_x, max_y) of a Cross from its body center."""
    ba = np.radians(body_angle_deg)
    sr = np.radians(spread_deg)
    a1, a2 = ba + sr, ba - sr
    max_x = arm_length * max(abs(np.cos(a1)), abs(np.cos(a2)))
    max_y = arm_length * max(abs(np.sin(a1)), abs(np.sin(a2)))
    return max_x, max_y


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    scale_options = np.linspace(0.5, 0.7, 4)
    scale2_options = np.linspace(0.4, 0.6, 4)
    center_x_options = np.linspace(0.4, 0.7, 5)
    height_options = np.linspace(0.0, 0.075, 2)
    left_options = [True, False]

    scale = rng.choice(scale_options)
    scale2 = rng.choice(scale2_options)
    center_x_frac = rng.choice(center_x_options)
    height = rng.choice(height_options)
    left = rng.choice(left_options)

    bar_thickness = 0.2
    spread = 77.5

    purple_ground = Bar(
        left=MIN_X,
        right=MAX_X,
        y=MIN_Y + height * WORLD_HEIGHT + bar_thickness / 2,
        thickness=bar_thickness,
        color="purple",
        dynamic=False,
    )

    # Static base: Cross at body_angle=0, bars at ±77.5° from horizontal (standingsticks default).
    arm_base = scale * WORLD_WIDTH / 3
    base_ext_x, base_ext_y = _cross_extents(arm_base, 0.0, spread)
    base_body_x = MIN_X + center_x_frac * WORLD_WIDTH
    base_body_y = purple_ground.top + base_ext_y

    base = Cross(
        x=base_body_x,
        y=base_body_y,
        angle=0.0,
        spread=spread,
        arm_length=arm_base,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Dynamic falling standingstick leaning against the base at angle=±35°.
    # Positioned so its edge is just past base.left/right and its bottom is slightly
    # below base.top — replicates PHYRE placement (right=base.left+0.1*scale2*W,
    # bottom=base.top-0.1*scale2*H).
    arm2 = scale2 * WORLD_WIDTH / 3
    sticks_angle = 35.0 if left else -35.0
    sticks_ext_x, sticks_ext_y = _cross_extents(arm2, sticks_angle, spread)

    if left:
        right_sticks = (base_body_x - base_ext_x) + 0.1 * scale2 * WORLD_WIDTH
        body_x_sticks = right_sticks - sticks_ext_x
    else:
        left_sticks = (base_body_x + base_ext_x) - 0.1 * scale2 * WORLD_WIDTH
        body_x_sticks = left_sticks + sticks_ext_x

    bottom_sticks = (base_body_y + base_ext_y) - 0.1 * scale2 * WORLD_HEIGHT
    body_y_sticks = bottom_sticks + sticks_ext_y

    falling_sticks = Cross(
        x=body_x_sticks,
        y=body_y_sticks,
        angle=sticks_angle,
        spread=spread,
        arm_length=arm2,
        thickness=bar_thickness,
        color="green",
        dynamic=True,
    )

    red_ball_1 = Ball(x=-3.0, y=4.0, radius=0.5, color="red", dynamic=True)
    red_ball_2 = Ball(x=3.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "base": base,
        "falling_sticks": falling_sticks,
        "purple_ground": purple_ground,
        "red_ball_1": red_ball_1,
        "red_ball_2": red_ball_2,
    }

    return Level(
        name="task00122",
        objects=objects,
        action_objects=["red_ball_1", "red_ball_2"],
        success_condition=success_condition,
        metadata={"description": "Make the falling sticks touch the ground."},
    )
