"""Registry for validated level entries.

Two-tier lookup:
  Tier 1 — bundled lzma-compressed JSON shipped with the package
            (interphyre/data/scenes/{level_name}.json.lzma). Loaded lazily
            per level, cached in-memory as {(seed, variant): entry}. O(1)
            after first access per level.
  Tier 2 — user SQLite cache at ~/.cache/interphyre/seed_registry.db,
            following the XDG convention used by PHYRE (~/.cache/phyre/).
            Configurable via INTERPHYRE_CACHE_DIR env var. WAL mode,
            check_same_thread=False for safe multi-threaded prewarm.

Writes always go to SQLite. Reads check bundled data first, then SQLite.

Schema hash: on first access to bundled data for a level, SeedRegistry
recomputes SHA-256 of the attribute key structure from extract_scene_dict
(build_level(seed=0)) and compares it to the stored schema_hash field.
On mismatch, a WARNING is logged and the bundled tier is skipped for that
level — live validation continues via SQLite. This prevents stale bundled
geometry from being served silently after constructor changes.
"""

from __future__ import annotations

import hashlib
import json
import logging
import lzma
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from interphyre.level import Level

logger = logging.getLogger(__name__)

# Bundled scenes live at interphyre/data/scenes/ relative to this package.
_SCENES_DIR = Path(__file__).parent.parent / "data" / "scenes"


@dataclass
class ValidatedLevel:
    """A level that has passed trivial and solvability checks.

    Bundles the level with its provenance so experiments can cite it exactly.
    The (level_name, seed, variant) triple is the short-form reference;
    scene_dict is the long-form reproducibility artifact.
    """

    level: Level
    level_name: str
    seed: int
    variant: int
    scene_dict: dict  # full geometry, JSON-serializable


def _default_cache_path() -> Path:
    """Return the default SQLite cache path, respecting INTERPHYRE_CACHE_DIR."""
    cache_dir_env = os.environ.get("INTERPHYRE_CACHE_DIR")
    cache_dir = (
        Path(cache_dir_env) if cache_dir_env else Path.home() / ".cache" / "interphyre"
    )
    return cache_dir / "seed_registry.db"


def _compute_schema_hash(level_name: str) -> str:
    """Return SHA-256 of the attribute key structure for level_name at seed=0.

    Hashes {object_name: sorted_attr_names} from extract_scene_dict applied
    to build_level(seed=0, variant=0). Detects constructor changes (new
    attributes, renames) that would make stored scene dicts produce wrong
    geometry on round-trip.

    Deferred imports break the import cycle: registry <- levels <- validation.
    """
    from interphyre.levels import load_level
    from interphyre.validation.checks import extract_scene_dict

    level = load_level(level_name, seed=0, variant=0)
    scene = extract_scene_dict(level)
    schema_repr = {name: sorted(attrs.keys()) for name, attrs in scene.items()}
    schema_str = json.dumps(schema_repr, sort_keys=True)
    return hashlib.sha256(schema_str.encode()).hexdigest()


class SeedRegistry:
    """Two-tier registry for validated (level_name, seed, variant) entries."""

    def __init__(self, cache_path: str | Path | None = None):
        """
        Args:
            cache_path: Override for the SQLite cache path. When None, uses
                ~/.cache/interphyre/seed_registry.db or INTERPHYRE_CACHE_DIR.
        """
        resolved = Path(cache_path) if cache_path else _default_cache_path()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        self._db_path = resolved

        # Per-level in-memory bundled cache: missing key = not yet loaded;
        # empty dict = no bundled data (file absent or schema stale).
        self._bundled: dict[str, dict[tuple[int, int], dict]] = {}
        self._schema_checked: set[str] = set()

        # Per-level schema hash cache: computed once per session per level.
        # Used to validate SQLite entries so stale cached results (written by
        # an older oracle or constructor) are treated as cache misses.
        self._current_schema_hashes: dict[str, str] = {}

        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS seed_validity (
                level_name    TEXT    NOT NULL,
                seed          INTEGER NOT NULL,
                variant       INTEGER NOT NULL DEFAULT 0,
                status        TEXT    NOT NULL,
                scene_json    TEXT,
                checked_at    TEXT    NOT NULL,
                solution_json TEXT,
                schema_hash   TEXT,
                PRIMARY KEY (level_name, seed, variant)
            )
        """)
        # Add columns to tables created before this schema version.
        # SQLite raises OperationalError when the column already exists; we
        # suppress it so these blocks are safe to run on both new and old databases.
        for col_def in (
            "ALTER TABLE seed_validity ADD COLUMN solution_json TEXT DEFAULT NULL",
            "ALTER TABLE seed_validity ADD COLUMN schema_hash TEXT DEFAULT NULL",
        ):
            try:
                self._conn.execute(col_def)
            except sqlite3.OperationalError:
                pass
        self._conn.commit()

    @property
    def db_path(self) -> Path:
        return self._db_path

    def _get_current_schema_hash(self, level_name: str) -> str:
        """Return the current schema hash for level_name, computing it once per session."""
        if level_name not in self._current_schema_hashes:
            self._current_schema_hashes[level_name] = _compute_schema_hash(level_name)
        return self._current_schema_hashes[level_name]

    def _load_bundled(self, level_name: str) -> None:
        """Load and validate bundled lzma data for level_name into memory.

        If the bundle file is absent, _bundled[level_name] is set to an empty
        dict (no bundled data available; falls through to SQLite).

        If the schema hash mismatches, a WARNING is logged, _bundled[level_name]
        is set to an empty dict, and the bundled tier is skipped for this level
        for the remainder of the process. Experiment continues via SQLite.
        """
        self._schema_checked.add(level_name)
        bundle_path = _SCENES_DIR / f"{level_name}.json.lzma"

        if not bundle_path.exists():
            self._bundled[level_name] = {}
            return

        with lzma.open(bundle_path, "rt", encoding="utf-8") as fh:
            data = json.load(fh)

        stored_hash = data.get("schema_hash", "")
        current_hash = self._get_current_schema_hash(level_name)

        if stored_hash != current_hash:
            logger.warning(
                "SeedRegistry: bundled data for '%s' has a stale schema hash "
                "(stored=%.8s, current=%.8s). Bundled tier will be skipped "
                "for this level. Run `python -m interphyre.validation._bundle` "
                "to regenerate.",
                level_name,
                stored_hash,
                current_hash,
            )
            self._bundled[level_name] = {}
            return

        entries = data.get("entries", [])
        # Preserve all entry fields including "solution" (present in bundles
        # generated after the solver-registry refactor; absent in older bundles
        # where entry.get("solution") will return None, which is the correct
        # default — solution unavailable for pre-refactor bundles).
        self._bundled[level_name] = {
            (entry["seed"], entry["variant"]): entry for entry in entries
        }
        logger.debug(
            "SeedRegistry: loaded bundle for '%s' (%d entries, oracle_commit=%s)",
            level_name,
            len(entries),
            data.get("oracle_commit", "unknown"),
        )

    def _ensure_bundled(self, level_name: str) -> None:
        """Load bundled data for level_name on first access."""
        if level_name not in self._schema_checked:
            self._load_bundled(level_name)

    def lookup(self, level_name: str, seed: int, variant: int = 0) -> str | None:
        """Return the status string for (level_name, seed, variant), or None.

        Checks bundled data first (O(1) in-memory after first access per level),
        then falls back to user SQLite cache.
        """
        self._ensure_bundled(level_name)

        entry = self._bundled.get(level_name, {}).get((seed, variant))
        if entry is not None:
            return entry["status"]

        row = self._conn.execute(
            "SELECT status, schema_hash FROM seed_validity WHERE level_name=? AND seed=? AND variant=?",
            (level_name, seed, variant),
        ).fetchone()
        if row is None:
            return None
        stored_hash = row[1]
        # Treat NULL or mismatched schema_hash as a cache miss so stale entries
        # written by an older oracle or constructor are re-validated automatically.
        if stored_hash != self._get_current_schema_hash(level_name):
            return None
        return row[0]

    def record(
        self,
        level_name: str,
        seed: int,
        variant: int,
        status: str,
        scene_dict: dict | None = None,
        solution: list | None = None,
    ) -> None:
        """Write or overwrite an entry in the user SQLite cache.

        solution, when provided, is a list of [x, y, radius] lists — one per
        action object.  Stored as JSON in solution_json and retrievable via
        get_solution().
        """
        scene_json = json.dumps(scene_dict) if scene_dict is not None else None
        solution_json = json.dumps(solution) if solution is not None else None
        schema_hash = self._get_current_schema_hash(level_name)
        checked_at = datetime.now(tz=timezone.utc).isoformat()
        self._conn.execute(
            """
            INSERT OR REPLACE INTO seed_validity
                (level_name, seed, variant, status, scene_json, checked_at, solution_json, schema_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (level_name, seed, variant, status, scene_json, checked_at, solution_json, schema_hash),
        )
        self._conn.commit()

    def get_scene_dict(self, level_name: str, seed: int, variant: int) -> dict | None:
        """Return the stored scene dict from bundled data or SQLite, or None."""
        self._ensure_bundled(level_name)

        entry = self._bundled.get(level_name, {}).get((seed, variant))
        if entry is not None:
            return entry.get("scene")

        row = self._conn.execute(
            "SELECT scene_json FROM seed_validity WHERE level_name=? AND seed=? AND variant=?",
            (level_name, seed, variant),
        ).fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return None

    def get_solution(self, level_name: str, seed: int, variant: int) -> list | None:
        """Return the stored solution from bundled data or SQLite, or None.

        The solution is a list of [x, y, radius] lists — one per action object —
        representing the winning placement found by the solver.  Returns None when
        no solution was recorded (levels without a registered solver, impossible
        seeds, or bundles generated before the solver-registry refactor).
        """
        self._ensure_bundled(level_name)

        entry = self._bundled.get(level_name, {}).get((seed, variant))
        if entry is not None:
            return entry.get("solution")

        row = self._conn.execute(
            "SELECT solution_json FROM seed_validity WHERE level_name=? AND seed=? AND variant=?",
            (level_name, seed, variant),
        ).fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return None

    def count(self, level_name: str, status: str) -> int:
        """Count entries with the given status across both tiers.

        Deduplicates by (seed, variant): SQLite entries that are already
        present in the bundled tier are not double-counted.
        """
        self._ensure_bundled(level_name)

        bundled = self._bundled.get(level_name, {})
        bundled_count = sum(1 for e in bundled.values() if e["status"] == status)
        bundled_keys = set(bundled.keys())

        sql_rows = self._conn.execute(
            "SELECT seed, variant FROM seed_validity WHERE level_name=? AND status=?",
            (level_name, status),
        ).fetchall()
        sql_count = sum(1 for row in sql_rows if (row[0], row[1]) not in bundled_keys)

        return bundled_count + sql_count

    def valid_entries(self, level_name: str) -> list[tuple[int, int]]:
        """Return all (seed, variant) pairs with status 'valid', sorted by seed.

        Merges bundled and SQLite tiers; deduplicates by (seed, variant).
        """
        self._ensure_bundled(level_name)

        bundled = self._bundled.get(level_name, {})
        valid: set[tuple[int, int]] = {
            (seed, variant)
            for (seed, variant), entry in bundled.items()
            if entry["status"] == "valid"
        }

        sql_rows = self._conn.execute(
            "SELECT seed, variant FROM seed_validity WHERE level_name=? AND status='valid'",
            (level_name,),
        ).fetchall()
        for row in sql_rows:
            valid.add((row[0], row[1]))

        return sorted(valid, key=lambda pair: (pair[0], pair[1]))

    def bundle_valid_rate(self, level_name: str) -> float | None:
        """Return the fraction of bundled entries with status 'valid', or None if no bundle.

        Returns None when the level has no bundle file or the bundle is empty —
        callers should treat None as "unknown" rather than "0% valid".
        Used to warn before entering the oracle search loop on known-impossible
        or near-impossible levels.
        """
        self._ensure_bundled(level_name)
        bundled = self._bundled.get(level_name, {})
        if not bundled:
            return None
        total = len(bundled)
        valid = sum(1 for entry in bundled.values() if entry["status"] == "valid")
        return valid / total

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        self._conn.close()

    def __enter__(self) -> SeedRegistry:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
