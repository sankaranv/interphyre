"""
Tests for environment action placement validation geometry.
"""

import pytest

from interphyre.environment import PhyreEnv
from interphyre.level import Level
from interphyre.objects import Ball, Bar, Basket


def _make_validation_level():
    def success_condition(engine):
        return False

    objects = {
        "action_ball": Ball(x=-4.0, y=4.0, radius=0.5, color="red", dynamic=True),
        "static_ball": Ball(x=0.0, y=0.0, radius=0.5, color="green", dynamic=False),
        "bar": Bar(x=2.0, y=0.0, length=4.0, angle=0.0, thickness=0.2, dynamic=False),
        "basket": Basket(x=-2.0, y=0.0, bottom_width=2.0, enable_sensor=False),
    }
    return Level(
        name="validation_level",
        objects=objects,
        action_objects=["action_ball"],
        success_condition=success_condition,
        metadata={},
    )


@pytest.mark.fast
def test_is_within_bounds_edges():
    """Placement bounds should reject coordinates outside world limits."""
    env = PhyreEnv(level=_make_validation_level())
    assert env._is_within_bounds(0.0, 0.0, 0.5) is True
    assert env._is_within_bounds(5.0, 0.0, 0.6) is False
    assert env._is_within_bounds(-5.0, 0.0, 0.6) is False
    env.close()


@pytest.mark.fast
def test_would_collide_with_ball():
    """Collision check should flag overlap with existing balls."""
    env = PhyreEnv(level=_make_validation_level())
    assert env._would_collide_with_objects(0.2, 0.0, 0.5) is True
    assert env._would_collide_with_objects(3.5, 3.5, 0.2) is False
    env.close()


@pytest.mark.fast
def test_would_collide_with_bar():
    """Collision check should flag overlap with bars."""
    env = PhyreEnv(level=_make_validation_level())
    assert env._would_collide_with_objects(2.0, 0.0, 0.5) is True
    env.close()


@pytest.mark.fast
def test_would_collide_with_basket_wall():
    """Collision check should flag overlap with basket walls."""
    env = PhyreEnv(level=_make_validation_level())
    basket = env.level.objects["basket"]
    x = basket.x + basket.total_width / 2 - 0.05
    assert env._would_collide_with_objects(x, basket.y, 0.2) is True
    env.close()
