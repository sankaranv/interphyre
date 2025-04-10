import numpy as np
from phyre2.core.level import Level, Object


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)
    level = Level(
        name="touch_wall",
        description="Make the green ball touch the wall.",
        solution_tier="BALL",
        action_objects=["red_ball"],
    )

    # Wall placement
    place_left_wall = rng.choice([True, False])
    wall_x = -4.8 if place_left_wall else 4.8

    level.add_object(
        "wall",
        Object(
            name="wall",
            type="platform",
            position=[wall_x, 0],
            size=[0.2, 10.0],
            angle=90.0,
            color="black",
            dynamic=False,
        ),
    )

    # Shelf bar
    shelf_width = rng.uniform(3.5, 5.0)
    level.add_object(
        "shelf",
        Object(
            name="shelf",
            type="platform",
            position=[0.0, 2.0],
            size=[shelf_width, 0.2],
            angle=0.0,
            color="gray",
            dynamic=False,
        ),
    )

    # Side ramps
    level.add_object(
        "left_ramp",
        Object(
            name="left_ramp",
            type="platform",
            position=[-shelf_width / 2 + 0.4, 2.2],
            size=[0.4, 0.2],
            angle=65.0,
            color="gray",
            dynamic=False,
        ),
    )
    level.add_object(
        "right_ramp",
        Object(
            name="right_ramp",
            type="platform",
            position=[shelf_width / 2 - 0.4, 2.2],
            size=[0.4, 0.2],
            angle=-65.0,
            color="gray",
            dynamic=False,
        ),
    )

    # Ball parameters
    ball_r = rng.uniform(0.2, 0.4)
    ball_x = rng.uniform(-shelf_width / 2 + 0.4, shelf_width / 2 - 0.4)
    ball_y = rng.uniform(0.0, 3.0)

    level.add_object(
        "green_ball",
        Object(
            name="green_ball",
            type="ball",
            position=[ball_x, 2.0 + ball_y],
            size=ball_r,
            color="green",
            dynamic=True,
        ),
    )

    level.add_object(
        "red_ball",
        Object(
            name="red_ball",
            type="ball",
            position=[0.0, 4.0],
            size=0.45,
            color="red",
            dynamic=True,
        ),
    )

    level.set_goal("touching", ["green_ball", "wall"])
    return level
