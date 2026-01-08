"""
Extra intervention API tests for apply_impulse behavior.
"""

from unittest.mock import MagicMock

import pytest

from interphyre.engine import Box2DEngine
from interphyre.level import Level
from interphyre.objects import Ball
from interphyre.interventions.api import InterventionContext


def _make_level():
    def success_condition(engine):
        return False

    objects = {
        "ball": Ball(x=0.0, y=0.0, radius=0.5, dynamic=True),
    }
    return Level(
        name="impulse_level",
        objects=objects,
        action_objects=[],
        success_condition=success_condition,
        metadata={},
    )


@pytest.mark.fast
def test_apply_impulse_with_point_tracks_modification():
    engine = Box2DEngine(level=_make_level())
    body = engine.bodies["ball"]
    body.ApplyLinearImpulse = MagicMock()

    with InterventionContext(engine) as ctx:
        ctx.apply_impulse("ball", impulse=(1.5, -2.0), point=(0.25, 0.75))

    assert body.ApplyLinearImpulse.called
    assert ctx.modifications
    assert ctx.modifications[-1]["type"] == "apply_impulse"
