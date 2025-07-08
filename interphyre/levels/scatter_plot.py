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

    # Create ball.
    center = rng.uniform(0.4, 0.6)
    ball_x = MIN_X + center * scene_width
    ball_y = MAX_Y - 0.1 * scene_height  # 0.9 * scene_height from top
    ball_radius = 0.4

    green_ball = Ball(
        x=ball_x,
        y=ball_y,
        radius=ball_radius,
        color="green",
        dynamic=True,
    )

    # Calculate top boundary for stars
    top = ball_y - 5 * ball_radius

    # Create a bunch of stars (static balls)
    stars = []

    def gen_chain(start_x, start_y):
        angle = rng.uniform() * 2 * np.pi
        angle_diff = rng.uniform() * 2 * np.pi / 10
        chain_stars = [(start_x, start_y)]
        line_length = 1
        n_valid = 0
        max_points = rng.integers(15, 30)

        while n_valid < max_points:
            if line_length >= 3 and rng.uniform() < 0.2:
                x, y = chain_stars[rng.integers(len(chain_stars))]
                line_length = 1
                angle = rng.uniform() * 2 * np.pi
                angle_diff = rng.uniform() * 2 * np.pi / 10
            else:
                line_length += 1
                step = rng.uniform(0.5, 3 * ball_radius - 0.05)  # Scale appropriately
                angle += angle_diff
                dx, dy = step * np.cos(angle), step * np.sin(angle)
                x, y = chain_stars[-1]
                x += dx
                y += dy

            if y >= top:
                continue

            chain_stars.append((x, y))

            # Convert to normalized coordinates for bounds check
            norm_x = (x - MIN_X) / scene_width
            norm_y = (y - MIN_Y) / scene_height
            if 0.0 < norm_x < 1 and 0.0 < norm_y < 1:
                n_valid += 1

        return chain_stars

    # Generate star chains
    for i in range(2):
        start_x = MIN_X + (0.2 if i else 0.7) * scene_width
        start_y = MIN_Y + 0.5 * scene_height
        stars.extend(gen_chain(start_x, start_y))

    # Create star objects
    star_objects = {}
    for i, (x, y) in enumerate(stars):
        # Convert to normalized coordinates for bounds check
        norm_x = (x - MIN_X) / scene_width
        norm_y = (y - MIN_Y) / scene_height
        if 0 <= norm_x <= 1 and 0 <= norm_y <= 1:
            star_ball = Ball(
                x=x,
                y=y,
                radius=0.2,  # scale=0.05 converted to radius
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
        name="point_cloud",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=[],
        success_condition=success_condition,
        metadata={
            "description": "Get the green ball to the purple floor by navigating through the cloud of star obstacles."
        },
    )
