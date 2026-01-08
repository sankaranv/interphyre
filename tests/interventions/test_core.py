"""
Coverage for core intervention base classes.
"""

from unittest.mock import MagicMock

import pytest

from interphyre.interventions.core import Intervention, CallableIntervention


class _DummyIntervention(Intervention):
    def apply(self, engine):
        super().apply(engine)


@pytest.mark.fast
def test_intervention_base_repr_and_apply_noop():
    intervention = _DummyIntervention()
    assert repr(intervention) == "_DummyIntervention()"
    assert intervention.apply(MagicMock()) is None


@pytest.mark.fast
def test_callable_intervention_apply_and_repr():
    calls = []

    def record(engine):
        calls.append(engine)

    engine = MagicMock()
    intervention = CallableIntervention(record, name="record_call")
    intervention.apply(engine)

    assert calls == [engine]
    assert repr(intervention) == "CallableIntervention(name='record_call')"
