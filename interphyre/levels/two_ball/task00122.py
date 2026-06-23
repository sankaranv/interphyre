import numpy as np
from interphyre.objects import Ball, Bar
from interphyre.level import Level
from interphyre.config import MIN_X, MAX_X, MIN_Y, MAX_Y, WORLD_WIDTH, WORLD_HEIGHT
from interphyre.levels import register_level


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("falling_sticks", "purple_ground", success_time)


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed)

    scale_options = np.linspace(0.5, 0.7, 4)
    scale2_options = np.linspace(0.4, 0.6, 4)
    center_x_options = np.linspace(0.4, 0.7, 5)
    height_options = np.linspace(0.0, 0.075, 2)
    left_options = [True, False]

    scale = rng.choice(scale_options)
    scale2 = rng.choice(scale2_options)
    center_x = rng.choice(center_x_options)
    height = rng.choice(height_options)
    left = rng.choice(left_options)

    bar_thickness = 0.2
    # Purple ground: full-width, bottom at height*H above MIN_Y.
    purple_ground = Bar(
        left=MIN_X,
        right=MAX_X,
        y=MIN_Y + height * WORLD_HEIGHT + bar_thickness / 2,
        thickness=bar_thickness,
        color="purple",
        dynamic=False,
    )

    # Static upright base (approximating standingsticks): vertical bar on ground.
    base_length = scale * WORLD_WIDTH
    base_cx = MIN_X + center_x * WORLD_WIDTH
    base = Bar(
        top=purple_ground.top + base_length,
        bottom=purple_ground.top,
        x=base_cx,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Dynamic falling sticks: standingsticks tipped 35° from vertical ≡ angle=55° or 125°
    # from horizontal in our Bar convention. We rest the lower end on the base top edge.
    # This is an unstable equilibrium requiring a push to fall, matching the task intent.
    falling_length = scale2 * WORLD_WIDTH
    half = falling_length / 2
    # sin(125°) = sin(55°) = cos(35°) ≈ 0.819 — vertical projection of half-length
    # |cos(125°)| = sin(35°) ≈ 0.574 — horizontal projection of half-length
    sin_tilt = np.sin(np.radians(55.0))   # = 0.819
    cos_tilt = np.cos(np.radians(55.0))   # = 0.574

    if left:
        # Lower-right end rests on base right-edge top; bar rises to upper-left (angle=125°).
        falling_cx = base.right - cos_tilt * half
        falling_cy = base.top + sin_tilt * half
        falling_angle = 125.0
    else:
        # Lower-left end rests on base left-edge top; bar rises to upper-right (angle=55°).
        falling_cx = base.left + cos_tilt * half
        falling_cy = base.top + sin_tilt * half
        falling_angle = 55.0

    falling_sticks = Bar.from_point_and_angle(
        x=falling_cx,
        y=falling_cy,
        angle=falling_angle,
        length=falling_length,
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
