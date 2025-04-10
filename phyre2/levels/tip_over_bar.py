import numpy as np
from typing import cast
from phyre2.objects import Ball, Platform, Basket, PhyreObject
from phyre2.level import Level
from phyre2.levels import register_level


def success_condition(engine):
    # In this level, we define success as the green platform making contact with the purple platform.
    return engine.has_contact("green_platform", "purple_platform")


def build_level(seed=None) -> Level:
    rng = np.random.default_rng(seed)

    # Create initial objects using fixed values (which will then be randomized)
    objects = {}

    # Green platform (target): initial fixed values then randomized.
    # Old: Platform(0, -4.8, 1, 90, "green", True)
    green_platform = Platform(
        x=0.0,
        y=-4.8,
        length=1.0,
        angle=90.0,
        color="green",
        dynamic=True,
    )

    # Red ball (action object): Old: Ball(0, 0, 0.4, "red", True)
    red_ball = Ball(
        x=0.0,
        y=0.0,
        radius=0.4,
        color="red",
        dynamic=True,
    )

    # Black platform (barrier): Old: Platform(0, -4.8, 1, 0, "black", False)
    black_platform = Platform(
        x=0.0,
        y=-4.8,
        length=1.0,
        angle=0.0,
        color="black",
        dynamic=False,
    )

    # Purple platform (goal): Old: Platform(0, -4.95, 5, 0, "purple", False)
    purple_platform = Platform(
        x=0.0,
        y=-4.95,
        length=5.0,
        angle=0.0,
        color="purple",
        dynamic=False,
    )

    # Ceiling platform: Old: Platform(0, 0, 5, 0, "black", False)
    ceiling_platform = Platform(
        x=0.0,
        y=0.0,
        length=5.0,
        angle=0.0,
        color="black",
        dynamic=False,
    )

    # Randomize black platform attributes
    black_platform.length = rng.uniform(2, 4)
    black_platform.x = rng.uniform(-1.5, 1.5)
    black_platform.y = rng.uniform(-3, 3)

    # Randomize green platform (target) attributes:
    green_platform.length = rng.uniform(1, 1.5)
    sign = rng.choice([-1, 1])
    green_platform.x = black_platform.x + sign * (black_platform.length - 0.1)
    green_platform.y = black_platform.y + green_platform.length + 0.1

    # Randomize ceiling platform height
    ceiling_platform.y = black_platform.y + rng.uniform(
        green_platform.length + 1.5, green_platform.length + 3
    )
    # Clip ceiling height to keep it in a reasonable range (e.g., -4.99 to 4.99)
    ceiling_platform.y = np.clip(ceiling_platform.y, -4.99, 4.99)

    # Randomize red ball starting position
    red_ball.x = rng.uniform(-4.5, 4.5)
    red_ball.y = rng.uniform(-2, 4)

    # Assemble objects dictionary
    objects["green_platform"] = green_platform
    objects["red_ball"] = red_ball
    objects["black_platform"] = black_platform
    objects["purple_platform"] = purple_platform
    objects["ceiling_platform"] = ceiling_platform

    # Set up the level
    return Level(
        name="tip_over_bar",
        objects=cast(dict[str, PhyreObject], objects),
        action_objects=["red_ball"],
        target_object="green_platform",
        goal_object="purple_platform",
        success_condition=success_condition,
        metadata={
            "description": "Tip over the bar so it hits the ground.",
        },
    )


register_level("tip_over_bar")(build_level)
