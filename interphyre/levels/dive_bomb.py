import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.config import MAX_X, MAX_Y, MIN_X, MIN_Y


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "purple_pad", success_time)


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    # Level parameters
    green_ball_radius = rng.uniform(0.2, 0.47)
    bar_thickness = 0.2
    purple_pad_length = 1
    target_position = rng.uniform(0.35, 0.65)

    # Ensure ball fits on target pad
    max_ball_radius = (purple_pad_length - 0.05) / 2
    if green_ball_radius * 2 >= purple_pad_length:
        green_ball_radius = max_ball_radius
    purple_pad_left = MIN_X + target_position * (MAX_X - MIN_X)
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

    # Short barrier at left edge of pad
    short_barrier_length = 1
    short_barrier_x = purple_pad.left - bar_thickness / 2
    short_barrier_y = MIN_Y + bar_thickness / 2 + short_barrier_length / 2
    short_barrier = Bar.from_point_and_angle(
        x=short_barrier_x,
        y=short_barrier_y,
        angle=90.0,
        length=short_barrier_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Cannon parameters
    cannon_angle = rng.uniform(-50, -30)
    cannon_length = rng.uniform(3, 6)

    # Position cannon bottom at fixed height
    cannon_bottom_target = MIN_Y + 3.0

    # Calculate ramp properties
    ramp_length = 1.0
    ramp_angle = 10

    # Position cannon relative to barriers
    blocker_left_x = short_barrier_x - bar_thickness / 2
    cannon_right_x = blocker_left_x - 1.0

    # Calculate cannon left end X position
    cannon_left_x = cannon_right_x - cannon_length * np.cos(np.radians(cannon_angle))

    # Calculate cannon endpoint positions
    angle_rad = np.radians(cannon_angle)
    cannon_left_y = (
        cannon_bottom_target
        - cannon_length * np.sin(angle_rad)
        + (bar_thickness / 2) * np.cos(angle_rad)
    )

    # Calculate right endpoint Y
    cannon_right_y = cannon_left_y + cannon_length * np.sin(angle_rad)

    # Create cannon bottom using endpoints
    cannon_bottom = Bar.from_endpoints(
        x1=cannon_left_x,
        y1=cannon_left_y,
        x2=cannon_right_x,
        y2=cannon_right_y,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Store start/end positions for ball placement
    cannon_start_x = cannon_left_x
    cannon_start_y = cannon_left_y
    cannon_end_x = cannon_right_x
    cannon_end_y = cannon_right_y

    # Build exit ramp
    ramp_left_x = cannon_right_x - 0.2
    ramp_left_y = cannon_right_y  # Same bottom as cannon right end

    # Calculate ramp right end
    ramp_right_x = ramp_left_x + ramp_length * np.cos(np.radians(ramp_angle))
    ramp_right_y = ramp_left_y + ramp_length * np.sin(np.radians(ramp_angle))

    ramp = Bar.from_endpoints(
        x1=ramp_left_x,
        y1=ramp_left_y,
        x2=ramp_right_x,
        y2=ramp_right_y,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Build barrier stack on right side
    barrier_stack = []
    flat_barrier_width = 1.0
    base_top = right_floor.y + bar_thickness / 2  # Top surface of right_floor

    for i in range(5):
        # Each plank's bottom rests on previous bar's top
        stack_bar_bottom = base_top + i * bar_thickness
        stack_bar_y = stack_bar_bottom + bar_thickness / 2
        stack_bar_left = right_floor.left
        stack_bar_right = stack_bar_left + flat_barrier_width

        stack_bar = Bar(
            left=stack_bar_left,
            right=stack_bar_right,
            y=stack_bar_y,
            thickness=bar_thickness,
            color="black",
            dynamic=False,
        )
        barrier_stack.append(stack_bar)

    # Tall vertical barrier on top of stack
    top_plank = barrier_stack[-1]
    tall_barrier_length = short_barrier_length  # Same length as short barrier!
    tall_barrier_bottom = top_plank.y + bar_thickness / 2
    tall_barrier_y = tall_barrier_bottom + tall_barrier_length / 2
    tall_barrier_x = top_plank.left + bar_thickness / 2  # Left edge of plank stack

    tall_barrier = Bar.from_point_and_angle(
        x=tall_barrier_x,
        y=tall_barrier_y,
        angle=90.0,
        length=tall_barrier_length,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )

    # Place green ball on the cannon bottom surface
    ball_position_along_cannon = rng.uniform(0.0, 0.8)

    green_ball_x = cannon_start_x + ball_position_along_cannon * (
        cannon_end_x - cannon_start_x
    )

    # Calculate Y position on cannon surface
    cannon_surface_y_at_ball = (
        cannon_start_y
        + ball_position_along_cannon * (cannon_end_y - cannon_start_y)
        + bar_thickness / 2
    )

    # Raise ball by radius * 1.7 above surface (matches PHYRE)
    green_ball_y = cannon_surface_y_at_ball + green_ball_radius * 1.7

    green_ball = Ball(
        x=green_ball_x,
        y=green_ball_y,
        radius=green_ball_radius,
        color="green",
        dynamic=True,
    )

    # Ensure ball stays within scene bounds
    if green_ball.x - green_ball_radius < MIN_X:
        green_ball.x = MIN_X + green_ball_radius
    if green_ball.x + green_ball_radius > MAX_X:
        green_ball.x = MAX_X - green_ball_radius

    # Generate a gray ball with radius half that of the green ball
    gray_ball_radius = green_ball_radius * 0.5

    # Place gray ball further along in the cannon, ahead of green ball
    gray_ball_position = rng.uniform(ball_position_along_cannon + 0.15, 0.95)
    gray_ball_x = cannon_start_x + gray_ball_position * (cannon_end_x - cannon_start_x)

    # Calculate Y position on cannon surface at gray ball X
    cannon_surface_y_at_gray = (
        cannon_start_y
        + gray_ball_position * (cannon_end_y - cannon_start_y)
        + bar_thickness / 2
    )

    # Raise gray ball above surface
    gray_ball_y = cannon_surface_y_at_gray + gray_ball_radius * 2.6

    gray_ball = Ball(
        x=gray_ball_x,
        y=gray_ball_y,
        radius=gray_ball_radius,
        color="gray",
        dynamic=True,
    )

    # If gray ball extends past ramp start, ensure it clears the ramp
    if gray_ball.x + gray_ball.radius >= ramp.x1:
        ramp_surface_at_gray = ramp.y1 + bar_thickness / 2
        gray_ball.y = max(ramp_surface_at_gray + gray_ball.radius, gray_ball.y)

    # Cannon middle and top bars provide additional structure
    cannon_middle_spacing = green_ball_radius * 6
    cannon_middle_y = cannon_bottom.y + cannon_middle_spacing

    cannon_middle = Bar.offset_along_angle(
        base_x=cannon_bottom.x,
        base_y=cannon_bottom.y,
        angle=90,  # Vertical offset
        distance=cannon_middle_spacing,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    # Set the angle and length to match the base cannon
    cannon_middle.angle = cannon_angle
    cannon_middle.length = cannon_length

    # Top cannon bar
    cannon_top_spacing = green_ball_radius * 10
    cannon_top_y = cannon_bottom.y + cannon_top_spacing

    cannon_top = Bar.offset_along_angle(
        base_x=cannon_bottom.x,
        base_y=cannon_bottom.y,
        angle=90,  # Vertical offset
        distance=cannon_top_spacing,
        thickness=bar_thickness,
        color="black",
        dynamic=False,
    )
    # Set the angle and length to match the base cannon
    cannon_top.angle = cannon_angle
    cannon_top.length = cannon_length

    # Calculate the right end of the ramp
    ramp_right_x = ramp.x + (ramp_length / 2) * np.cos(np.radians(ramp_angle))
    ramp_right_y = ramp.y + (ramp_length / 2) * np.sin(np.radians(ramp_angle))

    # Diagonal deflector bar at -30° to prevent overshooting
    deflector_angle = -30.0
    deflector_length = 5.0

    # Position deflector starting at ramp exit, aligned with cannon top level
    # Adjust vertical position to be at the level of the top cannon bar
    ramp_top_surface_y = ramp_right_y + bar_thickness / 2
    # Position deflector at approximately the same height as cannon_top
    vertical_offset = cannon_top.y - cannon_bottom.y  # Distance from bottom to top cannon
    deflector_start_y = ramp_top_surface_y + vertical_offset
    deflector_start_x = ramp_right_x

    # Deflector center position
    deflector_x = deflector_start_x + (deflector_length / 2) * np.cos(np.radians(deflector_angle))
    deflector_y = deflector_start_y + (deflector_length / 2) * np.sin(np.radians(deflector_angle))

    # Calculate corner for from_corner construction
    deflector_corner_x = deflector_x - (deflector_length / 2) * np.cos(np.radians(deflector_angle))
    deflector_corner_y = deflector_y - (deflector_length / 2) * np.sin(np.radians(deflector_angle))

    cannon_top_extension = Bar.from_corner(
        corner_x=deflector_corner_x,
        corner_y=deflector_corner_y,
        angle=deflector_angle,
        length=deflector_length,
        thickness=bar_thickness,
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
