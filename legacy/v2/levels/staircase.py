import numpy as np
from phyre2.core.level import Level, Object


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)
    level = Level(
        name="staircase",
        description="Make sure the green ball goes through the funnel and hits the purple pad",
        solution_tier="BALL",
        action_objects=["red_ball"],
    )

    # Add staircase platforms
    for i in range(5):
        level.add_object(
            f"stair_{i+1}_platform",
            Object(
                name=f"stair_{i+1}_platform",
                type="platform",
                position=[-4.5 + i * 2.0, 3.0 - i * 0.9],
                size=[0.7, 0.2],
                angle=-5,
                color="black",
                dynamic=False,
            ),
        )

    # Add green ball at top
    green_ball_x = rng.uniform(-4, 4)
    green_ball_r = rng.uniform(0.25, 0.4)
    level.add_object(
        "green_ball",
        Object(
            name="green_ball",
            type="ball",
            position=[green_ball_x, 4.9],
            size=green_ball_r,
            color="green",
            dynamic=True,
        ),
    )

    # Add red action ball
    red_ball_x = rng.uniform(-2.5, 4.5)
    red_ball_y = rng.uniform(-2, 4)
    level.add_object(
        "red_ball",
        Object(
            name="red_ball",
            type="ball",
            position=[red_ball_x, red_ball_y],
            size=0.4,
            color="red",
            dynamic=True,
        ),
    )

    # Add dynamic basket as goal target
    basket_scale = rng.uniform(1.0, 2.5)
    basket_y = 0 + basket_scale * 0.083
    level.add_object(
        "basket",
        Object(
            name="basket",
            type="basket",
            position=[0.0, basket_y],
            size=basket_scale,
            angle=0.0,
            color="purple",
            dynamic=True,
        ),
    )

    # Add barrier platforms to guide ball into basket
    barrier_length = basket_scale * 1.5
    level.add_object(
        "left_barrier_platform",
        Object(
            name="left_barrier_platform",
            type="platform",
            position=[-basket_scale * 0.83, 0.0],
            size=[barrier_length, 0.2],
            angle=90.0,
            color="black",
            dynamic=False,
        ),
    )
    level.add_object(
        "right_barrier_platform",
        Object(
            name="right_barrier_platform",
            type="platform",
            position=[basket_scale * 0.83, 0.0],
            size=[barrier_length, 0.2],
            angle=90.0,
            color="black",
            dynamic=False,
        ),
    )

    # Add ground platform
    level.add_object(
        "ground",
        Object(
            name="ground",
            type="platform",
            position=[0.0, 0.0],
            size=[10.0, 0.2],
            angle=0.0,
            color="black",
            dynamic=False,
        ),
    )

    level.set_goal("touching", ["green_ball", "basket"])
    return level
