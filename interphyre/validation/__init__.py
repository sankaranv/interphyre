"""Public API for the interphyre.validation module.

All functions that return levels return ValidatedLevel. The default global
registry is lazily initialized on first use — most callers need not instantiate
SeedRegistry directly.

Typical usage:

    from interphyre.validation import load_valid_level, iter_valid_levels

    # Load one valid level (bundled data: zero overhead for seeds 0–999)
    validated = load_valid_level("basket_case", seed=42)

    # Iterate over valid levels for an experiment loop
    for validated in iter_valid_levels("basket_case", start_seed=0):
        env = InterphyreEnv.from_level(validated.level)
        ...
        if enough_levels:
            break

    # Offline pre-warming before an experiment run
    counts = prewarm(["basket_case", "tipping_point"], range(5000), workers=8)
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterator
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

from interphyre.config import SimulationConfig
from interphyre.levels import load_level
from interphyre.validation.checks import extract_scene_dict, is_trivial
from interphyre.validation.oracles import get_oracle
from interphyre.validation.registry import SeedRegistry, ValidatedLevel

__all__ = [
    "ValidatedLevel",
    "extract_scene_dict",
    "validate_level",
    "load_valid_level",
    "iter_valid_levels",
    "prewarm",
]

logger = logging.getLogger(__name__)

# Deterministic salt for oracle RNG seeding.
# Using sum(b"oracle") avoids Python's randomized hash() across interpreter runs.
_ORACLE_RNG_SALT = sum(b"oracle")  # 630

# Module-level default registry — created once on first use.
_default_registry: SeedRegistry | None = None


def _get_registry() -> SeedRegistry:
    """Return the default global registry, creating it on first call."""
    global _default_registry
    if _default_registry is None:
        _default_registry = SeedRegistry()
    return _default_registry


def validate_level(
    level_name: str,
    seed: int,
    variant: int,
    *,
    registry: SeedRegistry | None = None,
    config: SimulationConfig | None = None,
    n_attempts: int = 50,
    oracle_steps: int = 500,
) -> str:
    """Run the full validation pipeline for one (level_name, seed, variant) triple.

    Returns the status string: "valid", "trivial", or "impossible".

    Pipeline:
        1. Registry lookup — return cached status immediately if present.
        2. load_level(level_name, seed, variant).
        3. No-action-objects check — levels with no action objects cannot be
           solved by the agent; mark "impossible".
        4. is_trivial check — if the success condition is met at t=0 with no
           agent action, mark "trivial".
        5. Oracle — run the targeted (or default) oracle; mark "valid" on
           success, "impossible" on exhaustion.

    The oracle RNG is seeded from (seed, variant, _ORACLE_RNG_SALT) so results
    are deterministic and independent of level geometry draws.
    """
    reg = registry if registry is not None else _get_registry()
    cfg = config or SimulationConfig()

    # Step 1: registry cache — skip full pipeline if already validated
    cached = reg.lookup(level_name, seed, variant)
    if cached is not None:
        return cached

    # Step 2: build the level geometry for this (seed, variant)
    level = load_level(level_name, seed=seed, variant=variant)

    # Step 3: levels with no action objects cannot be solved by agent placement
    if len(level.action_objects) == 0:
        reg.record(level_name, seed, variant, "impossible")
        return "impossible"

    # Step 4: trivial check — success already met without any agent action
    if is_trivial(level, cfg):
        reg.record(level_name, seed, variant, "trivial")
        return "trivial"

    # Step 5: oracle solvability search
    # RNG seeded from (seed, variant, salt) for reproducibility across processes.
    oracle = get_oracle(level_name)
    oracle_rng = np.random.default_rng([seed, variant, _ORACLE_RNG_SALT])
    solved = oracle(level, cfg, n_attempts, oracle_steps, oracle_rng)

    if solved:
        scene = extract_scene_dict(level)
        reg.record(level_name, seed, variant, "valid", scene_dict=scene)
        return "valid"
    else:
        reg.record(level_name, seed, variant, "impossible")
        return "impossible"


def load_valid_level(
    level_name: str,
    seed: int,
    *,
    registry: SeedRegistry | None = None,
    config: SimulationConfig | None = None,
    max_variants: int = 10,
    n_attempts: int = 50,
    oracle_steps: int = 500,
) -> ValidatedLevel:
    """Return a valid level for seed, trying variants 0, 1, … until one passes.

    Variant 0 is tried first: for seeds in the bundled range (0–999), the lookup
    hits in-memory bundled data with no I/O or oracle overhead.

    Raises RuntimeError if no valid variant is found within max_variants tries.
    """
    reg = registry if registry is not None else _get_registry()
    cfg = config or SimulationConfig()

    for variant in range(max_variants):
        status = validate_level(
            level_name,
            seed,
            variant,
            registry=reg,
            config=cfg,
            n_attempts=n_attempts,
            oracle_steps=oracle_steps,
        )
        if status == "valid":
            # Retrieve scene dict from registry (bundled or SQLite).
            scene = reg.get_scene_dict(level_name, seed, variant)
            level = load_level(level_name, seed=seed, variant=variant)
            if scene is None:
                # Fallback: re-extract if registry did not store the scene.
                # Should not happen in practice — validate_level always stores it.
                scene = extract_scene_dict(level)
            return ValidatedLevel(
                level=level,
                level_name=level_name,
                seed=seed,
                variant=variant,
                scene_dict=scene,
            )

    raise RuntimeError(
        f"load_valid_level: '{level_name}' seed={seed} has no valid variant in "
        f"[0, {max_variants}). Increase max_variants or audit oracle coverage "
        "with list_oracles()."
    )


def iter_valid_levels(
    level_name: str,
    start_seed: int = 0,
    *,
    registry: SeedRegistry | None = None,
    config: SimulationConfig | None = None,
    max_variants: int = 10,
    n_attempts: int = 50,
    oracle_steps: int = 500,
) -> Iterator[ValidatedLevel]:
    """Yield valid levels for seed, seed+1, seed+2, … without bound.

    The primary interface for experiment loops. Seed is incremented after each
    yield; variant search is handled transparently by load_valid_level.
    """
    reg = registry if registry is not None else _get_registry()
    cfg = config or SimulationConfig()
    seed = start_seed

    while True:
        try:
            yield load_valid_level(
                level_name,
                seed,
                registry=reg,
                config=cfg,
                max_variants=max_variants,
                n_attempts=n_attempts,
                oracle_steps=oracle_steps,
            )
        except RuntimeError:
            # Seed exhausted all variants — skip and continue to the next seed.
            # Callers who need to know the exhaustion rate should use prewarm().
            pass
        seed += 1


def _prewarm_worker(args: tuple) -> tuple[str, int, str]:
    """Validate one (level_name, seed) pair in a worker process.

    Each worker creates its own SeedRegistry — WAL mode on the shared SQLite
    database ensures safe concurrent writes without coordination.

    Returns (level_name, seed, outcome) where outcome is one of:
      "valid"      — a valid variant was found
      "trivial"    — all max_variants returned "trivial" (no agent needed)
      "impossible" — all max_variants returned "impossible" (oracle failed)
      "exhausted"  — max_variants exhausted with a mix of trivial and impossible
    """
    level_name, seed, cache_path, config, max_variants, n_attempts, oracle_steps = args

    # Deferred imports: each worker process loads its own module copies.
    from interphyre.validation import validate_level  # noqa: PLC0415
    from interphyre.validation.registry import SeedRegistry  # noqa: PLC0415

    registry = SeedRegistry(cache_path)

    statuses: list[str] = []
    for variant in range(max_variants):
        status = validate_level(
            level_name,
            seed,
            variant,
            registry=registry,
            config=config,
            n_attempts=n_attempts,
            oracle_steps=oracle_steps,
        )
        if status == "valid":
            return level_name, seed, "valid"
        statuses.append(status)

    # Exhausted all max_variants — categorise by what was found.
    unique = set(statuses)
    if unique == {"trivial"}:
        return level_name, seed, "trivial"
    elif unique == {"impossible"}:
        return level_name, seed, "impossible"
    else:
        return level_name, seed, "exhausted"


def _seed_outcome_from_registry(
    reg: SeedRegistry, level_name: str, seed: int, max_variants: int
) -> str | None:
    """Return the prewarm outcome for seed if all max_variants are in the registry.

    Returns None if any variant is not yet validated — the seed must be sent
    to the worker pool. Returns "valid" as soon as any valid variant is found,
    without checking the remaining variants.
    """
    statuses: list[str] = []
    for variant in range(max_variants):
        status = reg.lookup(level_name, seed, variant)
        if status is None:
            return None  # Still has unchecked variants — needs worker
        if status == "valid":
            return "valid"
        statuses.append(status)

    # All max_variants checked, none valid.
    unique = set(statuses)
    if unique == {"trivial"}:
        return "trivial"
    elif unique == {"impossible"}:
        return "impossible"
    else:
        return "exhausted"


def prewarm(
    level_names: list[str],
    seeds: range | list[int],
    *,
    registry: SeedRegistry | None = None,
    config: SimulationConfig | None = None,
    workers: int = 4,
    max_variants: int = 10,
    n_attempts: int = 50,
    oracle_steps: int = 500,
    progress: bool = True,
) -> dict[str, dict[str, int]]:
    """Pre-validate seeds for multiple levels in parallel.

    Idempotent: seeds fully resolved in the registry are counted without re-running
    the oracle. Seeds with partial coverage have only uncached variants validated.

    Uses ProcessPoolExecutor for CPU-bound oracle work. Shows a tqdm progress bar
    when progress=True and tqdm is installed; falls back to periodic stderr prints.

    Returns per-level outcome counts:
        {level_name: {"valid": N, "trivial": N, "impossible": N, "exhausted": N}}
    """
    reg = registry if registry is not None else _get_registry()
    cfg = config or SimulationConfig()
    cache_path = str(reg.db_path)
    seeds_list = list(seeds)

    counts: dict[str, dict[str, int]] = {
        name: {"valid": 0, "trivial": 0, "impossible": 0, "exhausted": 0}
        for name in level_names
    }

    # Partition seeds: fully resolved in registry vs. needs worker processing.
    pending: list[tuple] = []
    for level_name in level_names:
        for seed in seeds_list:
            outcome = _seed_outcome_from_registry(reg, level_name, seed, max_variants)
            if outcome is not None:
                counts[level_name][outcome] += 1
            else:
                pending.append(
                    (level_name, seed, cache_path, cfg, max_variants, n_attempts, oracle_steps)
                )

    if not pending:
        return counts

    # Set up progress reporting — tqdm if available, else periodic stderr prints.
    use_tqdm = False
    pbar = None
    if progress:
        try:
            from tqdm import tqdm as _tqdm  # noqa: PLC0415

            pbar = _tqdm(total=len(pending), desc="prewarm", unit="seed")
            use_tqdm = True
        except ImportError:
            pass

    completed = 0
    log_interval = max(1, len(pending) // 20)

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_prewarm_worker, args): args for args in pending}
        for future in as_completed(futures):
            level_name, _seed, outcome = future.result()
            counts[level_name][outcome] += 1
            completed += 1
            if use_tqdm and pbar is not None:
                pbar.update(1)
            elif progress and completed % log_interval == 0:
                print(
                    f"prewarm: {completed}/{len(pending)} done",
                    file=sys.stderr,
                )

    if use_tqdm and pbar is not None:
        pbar.close()

    return counts
