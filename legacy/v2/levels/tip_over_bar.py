import numpy as np
from phyre2.core.level import Level, Object


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)
    level = Level(
        name="tip_over_bar",
        description="Tip the bar over so it hits the ground.",
        solution_tier="BALL",
        action_objects=["red_ball"],
    )

    # Fixed objects
    black_length = rng.uniform(2, 4)
    black_x = rng.uniform(-1.5, 1.5)
    black_y = rng.uniform(-3, 3)

    green_length = rng.uniform(1, 1.5)
    green_x = black_x + rng.choice([-1, 1]) * (black_length - 0.1)
    green_y = black_y + green_length + 0.1

    ceiling_y = black_y + rng.uniform(green_length + 1.5, green_length + 3)
    ceiling_y = np.clip(ceiling_y, -4.99, 4.99)

    red_x = rng.uniform(-4.5, 4.5)
    red_y = rng.uniform(-2, 4)

    level.add_object(
        "green_platform",
        Object(
            name="green_platform",
            type="platform",
            position=[green_x, green_y],
            size=[green_length, 0.2],
            angle=90,
            color="green",
            dynamic=True,
        ),
    )

    level.add_object(
        "black_platform",
        Object(
            name="black_platform",
            type="platform",
            position=[black_x, black_y],
            size=[black_length, 0.2],
            angle=0,
            color="black",
            dynamic=False,
        ),
    )

    level.add_object(
        "purple_platform",
        Object(
            name="purple_platform",
            type="platform",
            position=[0, -4.95],
            size=[5, 0.2],
            angle=0,
            color="purple",
            dynamic=False,
        ),
    )

    level.add_object(
        "ceiling_platform",
        Object(
            name="ceiling_platform",
            type="platform",
            position=[0, ceiling_y],
            size=[5, 0.2],
            angle=0,
            color="black",
            dynamic=False,
        ),
    )

    level.add_object(
        "red_ball",
        Object(
            name="red_ball",
            type="ball",
            position=[red_x, red_y],
            size=0.4,
            color="red",
            dynamic=True,
        ),
    )

    level.set_goal("touching", ["green_platform", "purple_platform"])
    return level
