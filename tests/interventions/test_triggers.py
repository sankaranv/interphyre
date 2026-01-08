"""
Additional trigger and scheduler coverage for interventions.
"""

import logging
from unittest.mock import MagicMock

import pytest

from interphyre.engine import Box2DEngine
from interphyre.level import Level
from interphyre.objects import Ball
from interphyre.interventions.core import CallableIntervention
from interphyre.interventions.scheduler import InterventionScheduler
from interphyre.interventions.triggers import (
    EventBasedTrigger,
    ConditionBasedTrigger,
    TimeBasedTrigger,
    at_step,
    on_contact,
    on_contact_with,
    on_success,
    when,
    Trigger,
)


def _make_level(success=False):
    def success_condition(engine):
        return success

    objects = {
        "ball_a": Ball(x=0.0, y=0.0, radius=0.5, dynamic=False),
        "ball_b": Ball(x=0.0, y=0.0, radius=0.5, dynamic=False),
    }
    return Level(
        name="trigger_test",
        objects=objects,
        action_objects=[],
        success_condition=success_condition,
        metadata={},
    )


@pytest.mark.fast
def test_event_trigger_invalid_object_names():
    """Event trigger should reject invalid object_name counts."""
    engine = Box2DEngine(level=_make_level())
    trigger = EventBasedTrigger(event_type="contact", object_names=())
    with pytest.raises(ValueError, match="requires 1 or 2 object names"):
        trigger.should_fire(0, engine)


@pytest.mark.fast
def test_event_trigger_unknown_event_type():
    """Unknown event types should raise errors."""
    engine = Box2DEngine(level=_make_level())
    trigger = EventBasedTrigger(event_type="unknown", object_names=("ball_a",))
    with pytest.raises(ValueError, match="Unknown event type"):
        trigger.should_fire(0, engine)


@pytest.mark.fast
def test_condition_trigger_exception_logs(caplog):
    """Condition trigger should log and return False on exceptions."""
    engine = Box2DEngine(level=_make_level())

    def broken_condition(_engine):
        raise RuntimeError("boom")

    trigger = ConditionBasedTrigger(condition=broken_condition, once_only=False)
    with caplog.at_level(logging.WARNING):
        assert trigger.should_fire(0, engine) is False
        assert any("Condition evaluation failed" in rec.message for rec in caplog.records)


@pytest.mark.fast
def test_scheduler_disable_enable_and_history():
    """Scheduler should honor disable/enable and record execution history."""
    engine = Box2DEngine(level=_make_level())
    scheduler = InterventionScheduler(engine)

    intervention = CallableIntervention(lambda e: None, name="noop")
    trigger = TimeBasedTrigger(target_step=0, priority=0)
    scheduler.add(trigger, intervention)

    scheduler.disable()
    scheduler.check_triggers(0, engine)
    assert scheduler.get_executed_count() == 0

    scheduler.enable()
    scheduler.check_triggers(0, engine)
    assert scheduler.get_executed_count() == 1
    assert scheduler.get_execution_history()[0][0] == 0


class _PassThroughTrigger(Trigger):
    def should_fire(self, step_idx, engine):
        super().should_fire(step_idx, engine)
        return False


@pytest.mark.fast
def test_trigger_base_reset_noop():
    engine = Box2DEngine(level=_make_level())
    trigger = _PassThroughTrigger()
    assert trigger.should_fire(0, engine) is False
    assert trigger.reset() is None


@pytest.mark.fast
def test_time_based_trigger_repr_and_fire():
    engine = Box2DEngine(level=_make_level())
    trigger = at_step(3, priority=2)
    assert trigger.should_fire(2, engine) is False
    assert trigger.should_fire(3, engine) is True
    assert "TimeBasedTrigger(step=3, priority=2)" in repr(trigger)


@pytest.mark.fast
def test_event_trigger_contact_pairs_and_once_only():
    engine = Box2DEngine(level=_make_level())
    engine.contact_listener.contacts = {frozenset(("ball_a", "ball_b"))}

    trigger = on_contact("ball_a", "ball_b", once=True)
    assert trigger.should_fire(0, engine) is True
    assert trigger.should_fire(1, engine) is False
    trigger.reset()
    assert trigger.should_fire(2, engine) is True

    trigger_any = on_contact_with("ball_a", once=False)
    assert trigger_any.should_fire(0, engine) is True


@pytest.mark.fast
def test_event_trigger_success_condition():
    engine = Box2DEngine(level=_make_level(success=True))
    trigger = on_success()
    assert trigger.should_fire(0, engine) is True

    engine_false = Box2DEngine(level=_make_level(success=False))
    trigger_false = EventBasedTrigger(event_type="success", object_names=())
    assert trigger_false.should_fire(0, engine_false) is False


@pytest.mark.fast
def test_event_trigger_success_no_condition_returns_false():
    level = Level(
        name="trigger_no_condition",
        objects={"ball": Ball(x=0.0, y=0.0, radius=0.5, dynamic=False)},
        action_objects=[],
        success_condition=lambda e: True,
        metadata={},
    )
    level.success_condition = None
    engine = Box2DEngine(level=level)
    trigger = EventBasedTrigger(event_type="success", object_names=())
    assert trigger.should_fire(0, engine) is False


@pytest.mark.fast
def test_event_trigger_repr_and_reset():
    trigger = EventBasedTrigger(event_type="contact", object_names=("ball_a",))
    trigger._fired = True
    trigger.reset()
    assert trigger._fired is False
    assert "EventBasedTrigger(type=contact" in repr(trigger)


@pytest.mark.fast
def test_condition_trigger_once_only_reset_and_repr():
    engine = Box2DEngine(level=_make_level())

    def named_condition(_engine):
        return True

    trigger = when(named_condition, once=True, priority=1)
    assert trigger.should_fire(0, engine) is True
    assert trigger.should_fire(1, engine) is False
    trigger.reset()
    assert trigger.should_fire(2, engine) is True
    assert "ConditionBasedTrigger(condition=named_condition" in repr(trigger)

    class CallableCondition:
        def __call__(self, _engine):
            return False

    custom_trigger = when(CallableCondition(), once=False)
    assert "condition=custom" in repr(custom_trigger)
