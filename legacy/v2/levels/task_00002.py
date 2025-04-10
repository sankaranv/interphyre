import numpy as np
from phyre2.core.level import Level, Object


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)
    level = Level(
        name="avoid_obstacle",
        description="Drop the green ball to touch the ground without hitting the obstacle bar.",
        solution_tier="BALL",
        action_objects=["red_ball"],
    )

    # Obstacle dimensions and position (scaled for 10x10 world, y ∈ [0, 10])
    obstacle_width = rng.uniform(1.0, 7.0)
    obstacle_x = rng.uniform(-5.0, 5.0 - obstacle_width)
    obstacle_y = rng.uniform(3.0, 7.0)

    level.add_object(
        "obstacle",
        Object(
            name="obstacle",
            type="platform",
            position=[obstacle_x + obstacle_width / 2, obstacle_y],
            size=[obstacle_width, 0.2],
            angle=0.0,
            color="gray",
            dynamic=False,
        ),
    )

    # Ground bar (static)
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

    # Green ball above obstacle
    ball_r = 0.4
    level.add_object(
        "green_ball",
        Object(
            name="green_ball",
            type="ball",
            position=[obstacle_x + obstacle_width / 2, obstacle_y + 2.0],
            size=ball_r,
            color="green",
            dynamic=True,
        ),
    )

    # Red ball (action object)
    level.add_object(
        "red_ball",
        Object(
            name="red_ball",
            type="ball",
            position=[0.0, 5.0],
            size=0.45,
            color="red",
            dynamic=True,
        ),
    )

    level.set_goal("touching", ["green_ball", "ground"])
    return level
