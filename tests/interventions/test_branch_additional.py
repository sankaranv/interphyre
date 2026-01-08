"""
Targeted coverage for branch helper paths.
"""

import pytest

from interphyre.interventions.branch import SimulationBranch
from interphyre.interventions.state import StateSnapshot


@pytest.mark.fast
def test_create_child_branch_defaults_to_parent_snapshot():
    snapshot = StateSnapshot(
        step_count=0,
        current_time=0.0,
        objects={},
        box2d_state=b"",
        contacts=frozenset(),
        contact_start_times={},
        level_hash="hash",
        metadata={},
    )
    parent = SimulationBranch(snapshot=snapshot)
    child = parent.create_child_branch()
    assert child.snapshot is snapshot
    assert child.parent_branch is parent
