import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.render import MAX_X, MAX_Y, MIN_X, MIN_Y


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "purple_pad", success_time)


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    # Generate the green ball with random radius
    green_ball_radius = rng.uniform(0.2, 0.4)

    # Set the angle of the cannon
    bar_thickness = 0.2
    cannon_angle = rng.uniform(-45, -15)
    cannon_length = rng.uniform(3, 6)
    cannon_bottom_y = rng.uniform(-2, 2)
    # Position cannon so it touches the left side of the screen
    cannon_bottom_x = (
        MIN_X + (cannon_length / 2) * np.cos(np.radians(cannon_angle)) - bar_thickness
    )
    cannon_bottom = Bar(
        x=cannon_bottom_x,
        y=cannon_bottom_y,
        length=cannon_length,
        thickness=bar_thickness,
        angle=cannon_angle,
        color="black",
        dynamic=False,
    )

    cannon_end_x = cannon_bottom.x + (cannon_length / 2) * np.cos(
        np.radians(cannon_angle)
    )
    cannon_end_y = cannon_bottom.y + (cannon_length / 2) * np.sin(
        np.radians(cannon_angle)
    )
    ramp_length = rng.uniform(0.8, 1.2)
    ramp_angle = 10
    ramp_x = cannon_end_x + (ramp_length / 2 - 0.05) * np.cos(np.radians(ramp_angle))
    ramp_y = cannon_end_y + (ramp_length / 2 - 0.05) * np.sin(np.radians(ramp_angle))

    ramp = Bar(
        x=ramp_x,
        y=ramp_y,
        length=ramp_length,
        thickness=bar_thickness,
        angle=ramp_angle,
        color="black",
        dynamic=False,
    )

    ramp_end_x = ramp.x + (ramp_length / 2) * np.cos(np.radians(ramp_angle))
    short_barrier_length = 1
    short_barrier_x = ramp_end_x + bar_thickness
    short_barrier_y = MIN_Y + bar_thickness / 2 + short_barrier_length / 2
    short_barrier = Bar(
        x=short_barrier_x,
        y=short_barrier_y,
        length=short_barrier_length,
        thickness=bar_thickness,
        angle=90.0,
        color="black",
        dynamic=False,
    )

    purple_pad_length = 1
    purple_pad_left = short_barrier.x + bar_thickness / 2
    purple_pad_right = purple_pad_left + purple_pad_length
    purple_pad = Bar(
        left=purple_pad_left,
        right=purple_pad_right,
        y=MIN_Y + bar_thickness / 2,
        thickness=bar_thickness,
        color="purple",
        dynamic=False,
    )

    left_floor = Bar(
        left=MIN_X,
        right=purple_pad.left,
        y=MIN_Y + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    right_floor = Bar(
        left=purple_pad.right,
        right=MAX_X,
        y=MIN_Y + bar_thickness / 2,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    tall_barrier_length = 2 * short_barrier_length
    tall_barrier_x = purple_pad.x + purple_pad_length / 2 + bar_thickness / 2
    tall_barrier_y = MIN_Y + bar_thickness / 2 + tall_barrier_length / 2
    tall_barrier = Bar(
        x=tall_barrier_x,
        y=tall_barrier_y,
        length=tall_barrier_length,
        thickness=bar_thickness,
        angle=90.0,
        color="black",
        dynamic=False,
    )

    barrier_stack = []
    flat_barrier_width = 1.0
    for i in range(5):
        stack_bar_left = tall_barrier.x + bar_thickness / 2
        stack_bar_right = stack_bar_left + flat_barrier_width
        stack_bar_y = MIN_Y + bar_thickness * (i + 1)
        stack_bar = Bar(
            left=stack_bar_left,
            right=stack_bar_right,
            y=stack_bar_y,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )
        barrier_stack.append(stack_bar)

    # Place green ball right above the bottom bar of the cannon at any position along the cannon
    ball_position_along_cannon = rng.uniform(0.0, 0.8)
    cannon_start_x = MIN_X
    cannon_start_y = cannon_bottom.y - (cannon_length / 2) * np.sin(
        np.radians(cannon_angle)
    )

    green_ball_x = cannon_start_x + ball_position_along_cannon * (
        cannon_end_x - cannon_start_x
    )
    green_ball_y = (
        cannon_start_y
        + ball_position_along_cannon * (cannon_end_y - cannon_start_y)
        + green_ball_radius * 2
    )

    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    # Generate a gray ball with radius half that of the green ball
    gray_ball_radius = green_ball_radius * 0.5

    # Place it further along in the cannon at a random point between the green ball and the tip of the ramp
    gray_ball_position = rng.uniform(ball_position_along_cannon + 0.1, 0.9)
    gray_ball_x = cannon_start_x + gray_ball_position * (cannon_end_x - cannon_start_x)
    gray_ball_y = (
        cannon_start_y
        + gray_ball_position * (cannon_end_y - cannon_start_y)
        + green_ball_radius * 2.5
    )

    gray_ball = Ball(
        x=gray_ball_x,
        y=gray_ball_y,
        radius=gray_ball_radius,
        color="gray",
        dynamic=True,
    )

    # At a random small height above the green ball, place another parallel black bar
    cannon_middle_height = (bar_thickness + 2 * green_ball_radius) * rng.uniform(
        1.5, 2.5
    )
    cannon_middle_y = cannon_bottom.y + cannon_middle_height
    cannon_middle = Bar(
        x=cannon_bottom.x,
        y=cannon_middle_y,
        length=cannon_length,
        thickness=0.2,
        angle=cannon_angle,
        color="black",
        dynamic=False,
    )

    # At a random small height above the middle bar, make the top bar of the cannon
    cannon_top_height = (bar_thickness + 2 * green_ball_radius) * rng.uniform(1.0, 2.0)
    cannon_top_y = cannon_middle_y + cannon_top_height
    cannon_top = Bar(
        x=cannon_bottom.x,
        y=cannon_top_y,
        length=cannon_length,
        thickness=0.2,
        angle=cannon_angle,
        color="black",
        dynamic=False,
    )

    cannon_top_gap = 4 * green_ball_radius + bar_thickness

    # Calculate the right end of the ramp
    ramp_right_x = ramp.x + (ramp_length / 2) * np.cos(np.radians(ramp_angle))
    ramp_right_y = ramp.y + (ramp_length / 2) * np.sin(np.radians(ramp_angle))

    # The extension should be rotated +5 degrees from the top bar, with its left end at the right end of the ramp
    cannon_top_extension_angle = cannon_angle + rng.uniform(10, 15)  # Rotate upward
    # Left end x is ramp_right_x
    cannon_top_extension_left_x = ramp_right_x
    # Left end y is on the line of the cannon_top bar (same as before)
    # y = y0 + (x - x0) * tan(angle)
    cannon_top_extension_left_y = cannon_top.y + (
        cannon_top_extension_left_x - cannon_top.x
    ) * np.tan(
        np.radians(cannon_angle)
    )  # Use original cannon_angle for left end positioning
    # Center is offset from left end by (length/2) along the new rotated angle
    cannon_top_extension_x = cannon_top_extension_left_x + (cannon_length / 2) * np.cos(
        np.radians(cannon_top_extension_angle) + 0.05
    )
    cannon_top_extension_y = cannon_top_extension_left_y + (cannon_length / 2) * np.sin(
        np.radians(cannon_top_extension_angle)
    )
    cannon_top_extension = Bar(
        x=cannon_top_extension_x,
        y=cannon_top_extension_y,
        length=cannon_length,
        thickness=bar_thickness,
        angle=cannon_top_extension_angle,
        color="black",
        dynamic=False,
    )

    # Randomly place a red ball in the scene
    red_ball = Ball(
        x=rng.uniform(MIN_X + 1, MAX_X - 1),
        y=rng.uniform(MIN_Y + 2, MAX_Y - 2),
        radius=0.4,
        color="red",
        dynamic=True,
    )

    objects = {
        "cannon_bottom": cannon_bottom,
        "cannon_middle": cannon_middle,
        "cannon_top": cannon_top,
        "cannon_top_extension": cannon_top_extension,
        "ramp": ramp,
        "short_barrier": short_barrier,
        "tall_barrier": tall_barrier,
        "purple_pad": purple_pad,
        "left_floor": left_floor,
        "right_floor": right_floor,
        "green_ball": green_ball,
        "gray_ball": gray_ball,
        "red_ball": red_ball,
    }

    # Add stack bars to objects
    for i, stack_bar in enumerate(barrier_stack):
        objects[f"stack_bar_{i}"] = stack_bar

    return Level(
        name="dive_bomb",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Get the green ball to touch the purple pad by navigating through the cannon obstacles."
        },
    )
