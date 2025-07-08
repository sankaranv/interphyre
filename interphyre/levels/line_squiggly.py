import numpy as np
from typing import cast
from interphyre.objects import Ball, Bar, PhyreObject
from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.render import MAX_X, MAX_Y, MIN_X, MIN_Y


def success_condition(engine):
    success_time = engine.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "purple_floor", success_time)


@register_level
def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    # Set properties of objects.
    scene_width = MAX_X - MIN_X
    scene_height = MAX_Y - MIN_Y

    ball_x = rng.uniform(-3, 0)
    ball_y = 4.5
    ball_radius = 0.4

    green_ball = Ball(
        x=ball_x,
        y=ball_y,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    # Create a bunch of stars (static balls)
    stars = []

    def _generate_line(start_x, start_y, base_angle, num_nodes, max_x):
        line_stars = [(start_x, start_y)]
        for _ in range(num_nodes):
            step = rng.uniform(0.5, 3 * ball_radius - 0.05)
            angle = base_angle + rng.uniform(-4.5, 4.5)
            dx, dy = step * np.cos(np.radians(angle)), step * np.sin(np.radians(angle))
            x, y = line_stars[-1]
            x += dx
            y += dy
            if x >= max_x:
                break
            line_stars.append((x, y))
        return line_stars

    # Generate star positions
    top = ball_y - 5 * ball_radius
    line_stars = []  # Store each line separately to check for gaps

    for i, y in enumerate(reversed(np.linspace(-4, top, 4))):
        num_stars = rng.integers(3, 8)
        base_angle = 5
        new_stars = _generate_line(MIN_X, y, base_angle, num_stars, MAX_X - 2)
        if i % 2:
            new_stars = [(MAX_X - (x - MIN_X), y) for x, y in new_stars]
        line_stars.append((y, new_stars))

    # Flatten all stars
    for y, line_star_list in line_stars:
        stars.extend(line_star_list)

    # Create star objects
    star_objects = {}
    for i, (x, y) in enumerate(stars):
        size = 0.2  # Convert scale to radius
        if MIN_X <= x <= MAX_X and MIN_Y <= y <= MAX_Y:
            star_ball = Ball(
                x=x,
                y=y,
                radius=size,
                color="black",
                dynamic=False,
            )
            star_objects[f"star_{i}"] = star_ball

    # Create bottom wall
    purple_floor = Bar(
        x=0.0,
        y=-4.9,
        length=scene_width,
        thickness=0.2,
        angle=0.0,
        color="purple",
        dynamic=False,
    )

    # Combine all objects
    objects = {
        "green_ball": green_ball,
        "purple_floor": purple_floor,
        **star_objects,
    }

    return Level(
        name="line_squiggly",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=[],
        success_condition=success_condition,
        metadata={
            "description": "Get the green ball to the bottom wall by navigating through the squiggly line of obstacles."
        },
    )
