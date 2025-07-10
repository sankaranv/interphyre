import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.render import MAX_X, MAX_Y, MIN_X, MIN_Y, WORLD_WIDTH


def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "purple_floor", success_time)


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    ball_x = rng.uniform(-3, 0)
    ball_y = 4.5
    ball_radius = 0.5

    green_ball = Ball(
        x=ball_x,
        y=ball_y,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    # Add a red ball as an action object
    red_ball = Ball(
        x=rng.uniform(MIN_X + 1, MAX_X - 1),
        y=rng.uniform(0, 4),
        radius=0.4,
        color="red",
        dynamic=True,
    )

    # Create a bunch of stars (static balls)
    stars = []

    star_radius = 0.2

    def _generate_line_with_gap(
        start_x, start_y, base_angle, num_nodes, max_x, forbidden_x
    ):

        line_stars = [(start_x, start_y)]
        x, y = start_x, start_y
        gap_size = 2 * ball_radius + 2 * star_radius + rng.uniform(0, 0.05)
        # Determine which side to place the gap based on green ball position
        scene_center = (MIN_X + MAX_X) / 2
        if forbidden_x < scene_center:
            # Green ball is on left, place gap on right side
            gap_idx = (
                rng.integers(num_nodes // 2, num_nodes - 1) if num_nodes > 2 else 1
            )
        else:
            # Green ball is on right, place gap on left side
            gap_idx = rng.integers(1, num_nodes // 2) if num_nodes > 2 else 1

        for i in range(num_nodes):
            if i == gap_idx:
                # Create a gap by using a larger step
                step = gap_size  # Large enough for ball to pass
                angle = base_angle + rng.uniform(-2, 2)
            else:
                # Normal small step
                step = rng.uniform(0.5, 2 * ball_radius + star_radius)
                angle = base_angle + rng.uniform(-4.5, 4.5)

            dx, dy = step * np.cos(np.radians(angle)), step * np.sin(np.radians(angle))
            x += dx
            y += dy
            if x >= max_x:
                break
            line_stars.append((x, y))

        return line_stars

    # Generate star positions
    top = ball_y - 5 * ball_radius
    bottom = -4
    line_stars = []

    for i, y in enumerate(reversed(np.linspace(bottom, top, 4))):
        num_stars = rng.integers(4, 8)
        base_angle = 5
        new_stars = _generate_line_with_gap(
            MIN_X, y, base_angle, num_stars, MAX_X - 2, forbidden_x=ball_x
        )
        if i % 2:
            new_stars = [(MAX_X - (x - MIN_X), y) for x, y in new_stars]
        line_stars.append((y, new_stars))

    # Flatten all stars
    for y, line_star_list in line_stars:
        stars.extend(line_star_list)

    # Create star objects
    star_objects = {}
    for i, (x, y) in enumerate(stars):
        if MIN_X <= x <= MAX_X and MIN_Y <= y <= MAX_Y:
            star_ball = Ball(
                x=x,
                y=y,
                radius=star_radius,
                color="black",
                dynamic=False,
            )
            star_objects[f"star_{i}"] = star_ball

    # Create bottom wall
    purple_floor = Bar(
        x=0.0,
        y=-4.9,
        length=WORLD_WIDTH,
        thickness=0.2,
        angle=0.0,
        color="purple",
        dynamic=False,
    )

    # Combine all objects
    objects = {
        "green_ball": green_ball,
        "red_ball": red_ball,
        "purple_floor": purple_floor,
        **star_objects,
    }

    return Level(
        name="line_squiggly",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        success_condition=success_condition,
        metadata={
            "description": "Get the green ball to the bottom wall by using the red ball to knock it through the squiggly line of obstacles."
        },
    )
