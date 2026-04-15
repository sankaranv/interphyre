"""Bundle solution validation — 25 tests, one per level, across all 10001 seeds.

Each test replays every seed in the level's bundle using the stored solution
and asserts 100% success. Seeds with status "impossible" are skipped.

Replay uses the oracle path (_run_attempt: reset_attempt + raw Box2D step loop)
to match how the "0% fragility" guarantee was established during bundle generation.
InterphyreEnv.step() uses a different reset path (full body teardown/rebuild) that
loses Box2D warm-start data and produces different trajectories for ~0.7% of seeds;
that discrepancy is tracked as a separate issue.

Mark: bundle_validation — run with pytest -m bundle_validation.
These are the correctness gate for the PR: a regression in any level's
bundle appears as a named test failure here.
"""

import pytest

from interphyre.config import SimulationConfig
from interphyre.engine import Box2DEngine
from interphyre.levels import build_level_from_scene
from interphyre.validation import _get_registry
from interphyre.validation.oracles import _run_attempt

_SEEDS = range(10001)
_ORACLE_STEPS = 500


def _validate_bundle(level_name: str) -> None:
    """Replay all valid seeds in a level's bundle and assert 100% success.

    Uses _run_attempt (oracle path) for replay: consistent with the fragility
    validation that confirmed 0% failure rate during bundle generation.
    """
    registry = _get_registry()
    config = SimulationConfig()
    failures: list[int] = []

    for seed in _SEEDS:
        entry = registry.get_valid_entry(level_name, seed)
        if entry is None or entry["status"] != "valid":
            continue

        level = build_level_from_scene(level_name, entry["scene"])
        engine = Box2DEngine(level, config)
        positions = [tuple(s) for s in entry["solution"]]
        success = _run_attempt(engine, level, positions, oracle_steps=_ORACLE_STEPS)

        if not success:
            failures.append(seed)

    assert not failures, (
        f"{level_name}: {len(failures)} seeds failed (first 10: {failures[:10]})"
    )


@pytest.mark.bundle_validation
def test_basket_case():
    _validate_bundle("basket_case")


@pytest.mark.bundle_validation
def test_catapult():
    _validate_bundle("catapult")


@pytest.mark.bundle_validation
def test_cliffhanger():
    _validate_bundle("cliffhanger")


@pytest.mark.bundle_validation
def test_dive_bomb():
    _validate_bundle("dive_bomb")


@pytest.mark.bundle_validation
def test_down_to_earth():
    _validate_bundle("down_to_earth")


@pytest.mark.bundle_validation
def test_end_of_line():
    _validate_bundle("end_of_line")


@pytest.mark.bundle_validation
def test_falling_into_place():
    _validate_bundle("falling_into_place")


@pytest.mark.bundle_validation
def test_flagpole_sitta():
    _validate_bundle("flagpole_sitta")


@pytest.mark.bundle_validation
def test_just_a_nudge():
    _validate_bundle("just_a_nudge")


@pytest.mark.bundle_validation
def test_keyhole():
    _validate_bundle("keyhole")


@pytest.mark.bundle_validation
def test_locust_swarm():
    _validate_bundle("locust_swarm")


@pytest.mark.bundle_validation
def test_marble_race():
    _validate_bundle("marble_race")


@pytest.mark.bundle_validation
def test_mind_the_gap():
    _validate_bundle("mind_the_gap")


@pytest.mark.bundle_validation
def test_off_the_rails():
    _validate_bundle("off_the_rails")


@pytest.mark.bundle_validation
def test_pass_the_parcel():
    _validate_bundle("pass_the_parcel")


@pytest.mark.bundle_validation
def test_pinball_machine():
    _validate_bundle("pinball_machine")


@pytest.mark.bundle_validation
def test_seesaw():
    _validate_bundle("seesaw")


@pytest.mark.bundle_validation
def test_staircase():
    _validate_bundle("staircase")


@pytest.mark.bundle_validation
def test_straight_face():
    _validate_bundle("straight_face")


@pytest.mark.bundle_validation
def test_the_cradle():
    _validate_bundle("the_cradle")


@pytest.mark.bundle_validation
def test_the_funnel():
    _validate_bundle("the_funnel")


@pytest.mark.bundle_validation
def test_tipping_point():
    _validate_bundle("tipping_point")


@pytest.mark.bundle_validation
def test_two_body_problem():
    _validate_bundle("two_body_problem")


@pytest.mark.bundle_validation
def test_wedge_issue():
    _validate_bundle("wedge_issue")


@pytest.mark.bundle_validation
def test_zebra_crossing():
    _validate_bundle("zebra_crossing")
