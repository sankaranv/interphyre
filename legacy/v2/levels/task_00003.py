import numpy as np
from phyre2.core.level import Level, Object


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)
    level = Level(
        name="knock_bar",
        description="Knock the vertical green bar against the wall using the red ball.",
        solution_tier="BALL",
        action_objects=["red_ball"],
    )

    # Randomize vase (jar) position
    jar_x = rng.uniform(-4.5, 4.5)
    bar_scale = rng.uniform(0.2, 0.5)
    jitter_x = rng.uniform(-2.0, 2.0)

    # Add static ground
    level.add_object(
        "ground",
        Object(
            name="ground",
            type="platform",
            position=[0, 0],
            size=[10.0, 0.2],
            angle=0.0,
            color="black",
            dynamic=False,
        ),
    )

    # Add vase (as a small dynamic platform, upside-down jar equivalent)
    level.add_object(
        "vase",
        Object(
            name="vase",
            type="platform",
            position=[jar_x, 0.1],
            size=[0.5, 0.2],
            angle=0.0,
            color="blue",
            dynamic=True,
        ),
    )

    # Add vertical green bar on top of vase with jitter
    level.add_object(
        "green_bar",
        Object(
            name="green_bar",
            type="platform",
            position=[jar_x + jitter_x, 4.0],
            size=[0.2, bar_scale * 10],
            angle=90.0,
            color="green",
            dynamic=True,
        ),
    )

    # Determine which wall is closer
    wall_x = -5 if abs(-5 - (jar_x + jitter_x)) < abs(5 - (jar_x + jitter_x)) else 5

    # Add side wall
    level.add_object(
        "side_wall",
        Object(
            name="side_wall",
            type="platform",
            position=[wall_x, 0.5],
            size=[10.0, 0.2],
            angle=90.0,
            color="black",
            dynamic=False,
        ),
    )

    # Add red action ball
    level.add_object(
        "red_ball",
        Object(
            name="red_ball",
            type="ball",
            position=[0.0, 6.0],
            size=0.4,
            color="red",
            dynamic=True,
        ),
    )

    level.set_goal("touching", ["green_bar", "side_wall"])
    return level
