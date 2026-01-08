"""
Additional scheduler coverage for clear/reset/repr behavior.
"""

import pytest

from interphyre.engine import Box2DEngine
from interphyre.level import Level
from interphyre.objects import Ball
from interphyre.interventions.core import CallableIntervention
from interphyre.interventions.scheduler import InterventionScheduler
from interphyre.interventions.triggers import TimeBasedTrigger


def _make_level():
    return Level(
        name="scheduler_level",
        objects={"ball": Ball(x=0.0, y=0.0, radius=0.5, dynamic=False)},
        action_objects=[],
        success_condition=lambda e: False,
        metadata={},
    )


@pytest.mark.fast
def test_scheduler_clear_and_pending_count():
    engine = Box2DEngine(level=_make_level())
    scheduler = InterventionScheduler(engine)
    trigger = TimeBasedTrigger(target_step=0, priority=0)
    intervention = CallableIntervention(lambda e: None, name="noop")

    scheduler.add(trigger, intervention)
    assert scheduler.get_pending_count() == 1

    scheduler.clear()
    assert scheduler.get_pending_count() == 0


@pytest.mark.fast
def test_scheduler_reset_clears_executed():
    engine = Box2DEngine(level=_make_level())
    scheduler = InterventionScheduler(engine)
    trigger = TimeBasedTrigger(target_step=0, priority=0)
    intervention = CallableIntervention(lambda e: None, name="noop")

    scheduler.add(trigger, intervention)
    scheduler.check_triggers(0, engine)
    assert scheduler.get_executed_count() == 1

    scheduler.reset()
    assert scheduler.get_pending_count() == 0
    assert scheduler.get_executed_count() == 0


@pytest.mark.fast
def test_scheduler_repr_includes_status_and_counts():
    engine = Box2DEngine(level=_make_level())
    scheduler = InterventionScheduler(engine)

    assert "InterventionScheduler(enabled" in repr(scheduler)
    scheduler.disable()
    assert "InterventionScheduler(disabled" in repr(scheduler)
