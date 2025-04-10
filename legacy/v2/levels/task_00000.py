import numpy as np
from phyre2.core.level import Level, Object


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)
    level = Level(
        name="touch_ball",
        description="Make the green ball touch the blue ball.",
        solution_tier="BALL",
        action_objects=["red_ball"],
    )

    # Sample parameters for green ball (on the ground)
    green_x = rng.uniform(-4.5, 4.5)
    green_r = rng.uniform(0.2, 0.34)

    # Sample blue ball position and radius, ensuring horizontal separation
    while True:
        blue_x = rng.uniform(-4.5, 4.5)
        blue_r = rng.uniform(0.12, 0.6)
        if abs(blue_x - green_x) >= (green_r + blue_r + 0.5):  # ensure spacing
            break

    # Add balls
    level.add_object(
        "green_ball",
        Object(
            name="green_ball",
            type="ball",
            position=[green_x, 0],
            size=green_r,
            color="green",
            dynamic=True,
        ),
    )

    level.add_object(
        "blue_ball",
        Object(
            name="blue_ball",
            type="ball",
            position=[blue_x, 0],
            size=blue_r,
            color="blue",
            dynamic=True,
        ),
    )

    level.add_object(
        "red_ball",
        Object(
            name="red_ball",
            type="ball",
            position=[rng.uniform(-4.5, 4.5), rng.uniform(2.5, 4.5)],
            size=0.45,
            color="red",
            dynamic=True,
        ),
    )

    # Define the goal: green and blue ball must touch
    level.set_goal("touching", ["green_ball", "blue_ball"])
    return level
