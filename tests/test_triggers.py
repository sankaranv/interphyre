"""Regression tests for the trigger system."""

from unittest.mock import MagicMock

import pytest

from interphyre.interventions.triggers import (
    ConditionBasedTrigger,
    when,
)


def _make_mock_engine():
    """Create a minimal mock engine for trigger evaluation."""
    engine = MagicMock()
    engine.bodies = {}
    return engine


class TestConditionBasedTriggerExceptionPropagation:
    """FIX-CONDITION-TRIGGER-EXCEPTION-SWALLOWING regression tests.

    Conditions that raise exceptions must propagate to the caller,
    not be silently caught and converted to False.
    """

    def test_value_error_propagates(self):
        engine = _make_mock_engine()

        def bad_condition(e):
            raise ValueError("user bug in condition")

        trigger = ConditionBasedTrigger(condition=bad_condition)
        with pytest.raises(ValueError, match="user bug in condition"):
            trigger.should_fire(step_index=0, engine=engine)

    def test_key_error_propagates(self):
        engine = _make_mock_engine()

        def missing_key(e):
            return e.bodies["nonexistent"].position.y < 0

        trigger = ConditionBasedTrigger(condition=missing_key)
        with pytest.raises(KeyError):
            trigger.should_fire(step_index=0, engine=engine)

    def test_type_error_propagates(self):
        engine = _make_mock_engine()

        def type_bug(e):
            return 1 + "string"  # guaranteed TypeError

        trigger = when(type_bug)
        with pytest.raises(TypeError):
            trigger.should_fire(step_index=0, engine=engine)

    def test_attribute_error_propagates(self):
        def attr_bug(e):
            return e.nonexistent_attr.subattr > 0

        trigger = ConditionBasedTrigger(condition=attr_bug)
        # MagicMock won't raise AttributeError, so use a plain object
        plain_engine = object()
        with pytest.raises(AttributeError):
            trigger.should_fire(step_index=0, engine=plain_engine)

    def test_valid_condition_still_works(self):
        """Sanity check: valid conditions still return correctly."""
        engine = _make_mock_engine()
        trigger = ConditionBasedTrigger(condition=lambda e: True)
        assert trigger.should_fire(step_index=0, engine=engine) is True

    def test_valid_false_condition_still_works(self):
        engine = _make_mock_engine()
        trigger = ConditionBasedTrigger(condition=lambda e: False)
        assert trigger.should_fire(step_index=0, engine=engine) is False
