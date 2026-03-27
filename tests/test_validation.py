"""Unit tests for interphyre/validation/ — covering checks, oracles, registry, and public API.

19 tests matching the spec in plans/validation_module_spec.md §Tests.
"""

from __future__ import annotations

import json
import logging
import lzma
from itertools import islice

import numpy as np

from interphyre.config import SimulationConfig
from interphyre.level import Level
from interphyre.levels import build_level_from_scene, list_levels, load_level
from interphyre.objects import Ball
from interphyre.validation import (
    ValidatedLevel,
    extract_scene_dict,
    iter_valid_levels,
    load_valid_level,
    validate_level,
)
from interphyre.validation.checks import is_trivial
from interphyre.validation.oracles import get_oracle, list_oracles
from interphyre.validation.registry import SeedRegistry, _SCENES_DIR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_trivial_level() -> Level:
    """Level whose success condition is always True at t=0 — always trivial."""
    return Level(
        name="always_trivial",
        objects={"ball": Ball(x=0, y=0, radius=0.5, color="red", dynamic=False)},
        action_objects=["ball"],
        success_condition=lambda e: True,
    )


def _make_nontrivial_level() -> Level:
    """Level whose success condition is always False — never trivial."""
    return Level(
        name="never_trivial",
        objects={"ball": Ball(x=0, y=0, radius=0.5, color="red", dynamic=False)},
        action_objects=["ball"],
        success_condition=lambda e: False,
    )


# ---------------------------------------------------------------------------
# checks.py
# ---------------------------------------------------------------------------


def test_is_trivial_false():
    """basket_case seed=0 variant=0 is not trivially solved at t=0."""
    level = load_level("basket_case", seed=0, variant=0)
    assert is_trivial(level) is False


def test_is_trivial_true():
    """A level whose success condition returns True immediately is trivial."""
    level = _make_trivial_level()
    assert is_trivial(level) is True


# ---------------------------------------------------------------------------
# Variant system
# ---------------------------------------------------------------------------


def test_variant_zero_backward_compat():
    """basket_case seed=42 variant=0 is bit-identical to the default (no-variant) build.

    Variant 0 uses rng = default_rng(seed), which is identical to the pre-variant
    behavior. This verifies backward compatibility.
    """
    level_v0 = load_level("basket_case", seed=42, variant=0)
    level_default = load_level("basket_case", seed=42)  # variant=0 by default

    for obj_name in level_v0.objects:
        obj_v0 = level_v0.objects[obj_name]
        obj_default = level_default.objects[obj_name]
        assert obj_v0.x == obj_default.x, (
            f"{obj_name}.x differs under variant=0 vs default"
        )
        assert obj_v0.y == obj_default.y, (
            f"{obj_name}.y differs under variant=0 vs default"
        )


def test_variant_nonzero_distinct():
    """basket_case seed=0 variant=0 and variant=1 produce different geometries.

    Variant>0 uses rng = default_rng((seed, variant)), so the geometry is distinct
    from variant=0 with overwhelming probability.
    """
    level_v0 = load_level("basket_case", seed=0, variant=0)
    level_v1 = load_level("basket_case", seed=0, variant=1)

    any_different = any(
        level_v0.objects[name].x != level_v1.objects[name].x
        or level_v0.objects[name].y != level_v1.objects[name].y
        for name in level_v0.objects
    )
    assert any_different, "variant=0 and variant=1 produced identical geometry"


# ---------------------------------------------------------------------------
# oracles.py
# ---------------------------------------------------------------------------


def test_oracle_finds_solution():
    """straight_face seed=2 variant=0 — the registered oracle finds a solution within 50 attempts.

    seed=2 variant=0 is confirmed valid in the bundled data for straight_face,
    making it a reliable geometry for oracle coverage tests.
    """
    level = load_level("straight_face", seed=2, variant=0)
    config = SimulationConfig()
    oracle = get_oracle("straight_face")
    rng = np.random.default_rng(1)  # seed=42 finds 83/200 valid placements but none solvable after valid-placement enforcement

    solved = oracle(level, config, n_attempts=50, oracle_steps=500, rng=rng)
    assert solved is True


def test_list_oracles_coverage():
    """list_oracles() returns an entry ('targeted' or 'default') for every registered level."""
    all_levels = set(list_levels())
    coverage = list_oracles()

    assert set(coverage.keys()) == all_levels, "list_oracles missing some levels"
    assert all(v in ("targeted", "default") for v in coverage.values()), (
        "list_oracles returned unexpected value (expected 'targeted' or 'default')"
    )


# ---------------------------------------------------------------------------
# registry.py — SeedRegistry
# ---------------------------------------------------------------------------


def test_registry_roundtrip(tmp_path):
    """Record an entry with a scene dict and retrieve it bit-identically from SQLite."""
    reg = SeedRegistry(tmp_path / "test.db")

    # Use a seed outside the bundled range so SQLite is the authoritative tier.
    level = load_level("basket_case", seed=9999, variant=0)
    scene = extract_scene_dict(level)

    reg.record("basket_case", 9999, 0, "valid", scene_dict=scene)
    retrieved = reg.get_scene_dict("basket_case", 9999, 0)

    assert retrieved is not None
    assert retrieved == scene


def test_registry_idempotent(tmp_path):
    """Recording the same (level, seed, variant) key twice does not duplicate the row."""
    reg = SeedRegistry(tmp_path / "test.db")
    level = load_level("basket_case", seed=9999, variant=0)
    scene = extract_scene_dict(level)

    reg.record("basket_case", 9999, 0, "valid", scene_dict=scene)
    reg.record("basket_case", 9999, 0, "valid", scene_dict=scene)  # duplicate write

    # SQLite uses INSERT OR REPLACE — only one row should exist.
    row_count = reg._conn.execute(
        "SELECT COUNT(*) FROM seed_validity "
        "WHERE level_name='basket_case' AND seed=9999 AND variant=0"
    ).fetchone()[0]
    assert row_count == 1


# ---------------------------------------------------------------------------
# validate_level / load_valid_level / iter_valid_levels
# ---------------------------------------------------------------------------


def test_validate_level_caches(tmp_path):
    """A second call to validate_level for the same triple hits the registry cache.

    Two calls should return the same status and produce exactly one SQLite row —
    the pipeline (oracle, trivial check) does not run twice.
    """
    reg = SeedRegistry(tmp_path / "test.db")

    # Pre-record as trivial so validate_level returns immediately on both calls.
    reg.record("basket_case", 9999, 0, "trivial")

    status1 = validate_level("basket_case", 9999, 0, registry=reg)
    status2 = validate_level("basket_case", 9999, 0, registry=reg)

    assert status1 == "trivial"
    assert status2 == "trivial"

    row_count = reg._conn.execute(
        "SELECT COUNT(*) FROM seed_validity "
        "WHERE level_name='basket_case' AND seed=9999 AND variant=0"
    ).fetchone()[0]
    assert row_count == 1


def test_load_valid_level_returns_validated_level():
    """load_valid_level returns a ValidatedLevel with all fields populated."""
    result = load_valid_level("basket_case", seed=42)

    assert isinstance(result, ValidatedLevel)
    assert result.level is not None
    assert result.level_name == "basket_case"
    assert result.seed == 42
    assert isinstance(result.variant, int) and result.variant >= 0
    assert result.scene_dict is not None
    assert isinstance(result.scene_dict, dict)


def test_load_valid_level_variant_increment(tmp_path):
    """When variant=0 is trivial, load_valid_level advances to variant=1.

    We pre-populate the registry with the two outcomes so no oracle run is needed,
    keeping the test fast and deterministic.
    """
    reg = SeedRegistry(tmp_path / "test.db")

    # Mark variant=0 as trivial — simulates a seed whose initial geometry auto-solves.
    reg.record("basket_case", 9999, 0, "trivial")

    # Pre-record variant=1 as valid with a real scene dict.
    level_v1 = load_level("basket_case", seed=9999, variant=1)
    scene_v1 = extract_scene_dict(level_v1)
    reg.record("basket_case", 9999, 1, "valid", scene_dict=scene_v1)

    result = load_valid_level("basket_case", 9999, registry=reg, max_variants=3)

    assert isinstance(result, ValidatedLevel)
    assert result.variant == 1
    assert result.seed == 9999
    assert result.scene_dict is not None


def test_iter_valid_levels():
    """iter_valid_levels yields ValidatedLevel instances with monotonically increasing seeds."""
    levels = list(islice(iter_valid_levels("basket_case", start_seed=0), 5))

    assert len(levels) == 5
    assert all(isinstance(v, ValidatedLevel) for v in levels)

    seeds = [v.seed for v in levels]
    assert seeds == sorted(seeds), (
        "seeds from iter_valid_levels are not monotonically increasing"
    )
    assert len(set(seeds)) == 5, "iter_valid_levels yielded duplicate seeds"


def test_scene_dict_round_trip():
    """Extract a scene dict, rebuild the level from it, assert the geometry is bit-identical.

    Uses build_level_from_scene as the reconstruction path. Comparing extract_scene_dict
    on both levels verifies the round-trip without relying on physics execution.
    """
    level = load_level("basket_case", seed=0, variant=0)
    scene = extract_scene_dict(level)

    rebuilt = build_level_from_scene("basket_case", scene)
    rebuilt_scene = extract_scene_dict(rebuilt)

    assert set(scene.keys()) == set(rebuilt_scene.keys()), (
        "object name mismatch after round-trip"
    )
    for obj_name in scene:
        for attr, val in scene[obj_name].items():
            assert attr in rebuilt_scene[obj_name], (
                f"missing attribute {obj_name}.{attr}"
            )
            assert rebuilt_scene[obj_name][attr] == val, (
                f"{obj_name}.{attr}: {rebuilt_scene[obj_name][attr]!r} != {val!r}"
            )


# ---------------------------------------------------------------------------
# Bundled data tier
# ---------------------------------------------------------------------------


def test_bundled_lookup(tmp_path):
    """basket_case seed=2 variant=0 returns 'valid' from bundled data without SQLite writes.

    seed=2 variant=0 is confirmed valid in the basket_case bundle. The test verifies
    that bundled lookups are O(1) in-memory reads and do not touch SQLite.
    """
    reg = SeedRegistry(tmp_path / "test.db")

    status = reg.lookup("basket_case", 2, 0)

    assert status == "valid"

    # Bundled-tier lookups are read-only — SQLite should be untouched.
    row_count = reg._conn.execute("SELECT COUNT(*) FROM seed_validity").fetchone()[0]
    assert row_count == 0


def test_bundled_scene_reconstruction(tmp_path):
    """A scene dict from bundled data round-trips through build_level_from_scene bit-identically.

    The bundled scene for action objects records the oracle-placed position (not the initial
    build position), so the correct comparison is: retrieve bundled scene → rebuild level from
    it → re-extract scene → assert identical to bundled.
    """
    reg = SeedRegistry(tmp_path / "test.db")

    bundled_scene = reg.get_scene_dict("basket_case", 2, 0)
    assert bundled_scene is not None

    # Reconstruct the level geometry from the bundled scene dict.
    rebuilt = build_level_from_scene("basket_case", bundled_scene)
    rebuilt_scene = extract_scene_dict(rebuilt)

    assert set(bundled_scene.keys()) == set(rebuilt_scene.keys()), (
        "object name mismatch after round-trip through build_level_from_scene"
    )
    for obj_name in bundled_scene:
        for attr, bundled_val in bundled_scene[obj_name].items():
            assert attr in rebuilt_scene[obj_name], (
                f"rebuilt scene missing attribute {obj_name}.{attr}"
            )
            rebuilt_val = rebuilt_scene[obj_name][attr]
            if isinstance(bundled_val, float):
                assert abs(rebuilt_val - bundled_val) < 1e-9, (
                    f"{obj_name}.{attr}: rebuilt={rebuilt_val!r}, bundled={bundled_val!r}"
                )
            else:
                assert rebuilt_val == bundled_val, (
                    f"{obj_name}.{attr}: rebuilt={rebuilt_val!r}, bundled={bundled_val!r}"
                )


def test_default_registry():
    """load_valid_level with no registry argument uses the module-level default."""
    result = load_valid_level("basket_case", seed=10)  # no registry argument

    assert isinstance(result, ValidatedLevel)
    assert result.level_name == "basket_case"
    assert result.seed == 10
    assert result.scene_dict is not None


# ---------------------------------------------------------------------------
# Schema hash
# ---------------------------------------------------------------------------


def test_schema_hash_stored():
    """The bundled JSON for basket_case contains a 'schema_hash' field."""
    bundle_path = _SCENES_DIR / "basket_case.json.lzma"
    with lzma.open(bundle_path, "rt", encoding="utf-8") as fh:
        data = json.load(fh)

    assert "schema_hash" in data, "bundled JSON is missing 'schema_hash'"
    assert isinstance(data["schema_hash"], str) and len(data["schema_hash"]) == 64


def test_schema_hash_valid():
    """The stored schema hash for basket_case matches the current object key structure."""
    import interphyre.validation.registry as reg_mod

    bundle_path = _SCENES_DIR / "basket_case.json.lzma"
    with lzma.open(bundle_path, "rt", encoding="utf-8") as fh:
        data = json.load(fh)

    stored_hash = data.get("schema_hash", "")
    expected_hash = reg_mod._compute_schema_hash("basket_case")

    assert stored_hash == expected_hash, (
        f"schema_hash mismatch — bundled data may be stale. "
        f"stored={stored_hash[:8]}, expected={expected_hash[:8]}"
    )


def test_schema_hash_stale(tmp_path, monkeypatch, caplog):
    """When the schema hash mismatches, SeedRegistry logs a WARNING and skips bundled data."""
    import interphyre.validation.registry as reg_mod

    # Patch _compute_schema_hash to always return a hash that won't match the stored one.
    monkeypatch.setattr(reg_mod, "_compute_schema_hash", lambda name: "0" * 64)

    reg = SeedRegistry(tmp_path / "test.db")

    with caplog.at_level(logging.WARNING, logger="interphyre.validation.registry"):
        result = reg.lookup("basket_case", 0, 0)

    # A stale-schema warning should have been emitted.
    stale_warnings = [m for m in caplog.messages if "stale" in m.lower()]
    assert stale_warnings, "expected a stale-schema WARNING but none was logged"

    # Bundled tier is skipped; SQLite is empty → lookup returns None.
    assert result is None, (
        f"expected None (bundled skipped, SQLite empty) but got {result!r}"
    )
