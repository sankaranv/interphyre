"""Generate webm preview videos for two-ball and virtual tools levels.

For each level, runs the registered oracle against seed 42 (falling back to
seeds 0-9 if 42 fails) to find a solution, then replays that solution with
the VideoRecorder and saves a webm to docs/assets/levels/.

Usage:
    cd /path/to/interphyre
    python tools/generate_previews.py
    python tools/generate_previews.py --levels bottoms_up crossing
    python tools/generate_previews.py --seed 0
"""

from __future__ import annotations

import argparse
import sys
import os

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

TWO_BALL_LEVELS = [
    "bottoms_up", "bug_eyes", "coin_drop", "crucifix", "deadbolt",
    "domino_effect", "double_dutch", "down_the_drain", "fire_escape",
    "guillotine", "meet_me_halfway", "missing_piece", "mouse_traps",
    "no_mans_land", "point_blank", "pole_vault", "room_divider",
    "seesaw_redux", "slot_machine", "star_crossed", "the_relay",
    "tip_the_scales", "trapeze", "trebuchet", "twin_peaks",
]

VT_LEVELS = [
    "the_offering", "crossing", "dead_weight", "free_fall", "floodgate",
    "low_bridge", "the_seal", "warden", "the_idol", "walk_the_plank",
    "the_scaffold", "hit_the_deck",
]

DEFAULT_SEED = 42
FALLBACK_SEEDS = list(range(100))
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "assets", "levels")


def _patch_run_attempt(oracle_module, winning_store: list) -> None:
    """Replace _run_attempt in every loaded oracle module to capture winners."""
    original = oracle_module._run_attempt

    def capturing(env, positions):
        result = original(env, positions)
        if result and not winning_store:
            winning_store.append(list(positions))
        return result

    # Patch package-level reference and every sub-module that imported it.
    oracle_module._run_attempt = capturing
    for name, mod in list(sys.modules.items()):
        if (
            name.startswith("interphyre.validation.oracles")
            and hasattr(mod, "_run_attempt")
            and mod is not oracle_module
        ):
            mod._run_attempt = capturing


def _restore_run_attempt(oracle_module, original) -> None:
    oracle_module._run_attempt = original
    for name, mod in list(sys.modules.items()):
        if (
            name.startswith("interphyre.validation.oracles")
            and hasattr(mod, "_run_attempt")
            and mod is not oracle_module
        ):
            mod._run_attempt = original


def find_solution(
    level_name: str, seed: int, oracle_fn, defaults: dict, config
) -> tuple[int, list] | tuple[None, None]:
    """Return (seed_used, positions) for the first seed that produces a solution."""
    from interphyre.levels import load_level
    import interphyre.validation.oracles as oracle_module

    seeds_to_try = [seed] + [s for s in FALLBACK_SEEDS if s != seed]

    original = oracle_module._run_attempt

    for s in seeds_to_try:
        winning_store: list = []
        _patch_run_attempt(oracle_module, winning_store)
        try:
            level = load_level(level_name, seed=s)
            rng = np.random.default_rng(s)
            n_attempts = defaults.get("n_attempts", 200)
            oracle_steps = config.max_steps
            oracle_fn(level, config, n_attempts, oracle_steps, rng)
        except Exception as exc:
            print(f"    oracle error (seed {s}): {exc}")
        finally:
            _restore_run_attempt(oracle_module, original)

        if winning_store:
            return s, winning_store[0]

    return None, None


def record_preview(level_name: str, seed: int, positions: list, config, output_path: str) -> None:
    from interphyre.levels import load_level
    from interphyre.environment import InterphyreEnv
    from interphyre.render.video import VideoRecorder

    level = load_level(level_name, seed=seed)
    recorder = VideoRecorder(output_path=output_path, video_format="webm", fps=30)
    env = InterphyreEnv(level, config=config, validate=False)
    env.renderer = recorder
    try:
        env.reset()
        env.step(positions)
    finally:
        recorder.close()
        env.renderer = None
        env.close()


def _random_positions(level_name: str, seed: int, config) -> list | None:
    """Return a plausible random action for levels where the oracle finds nothing.

    Samples near the action objects' default positions so the placed balls at
    least start close to the scene rather than in random empty space.
    """
    from interphyre.levels import load_level
    from interphyre.objects import Ball

    try:
        level = load_level(level_name, seed=seed)
    except Exception:
        return None

    rng = np.random.default_rng(seed)
    positions = []
    for name in level.action_objects:
        obj = level.objects[name]
        r = float(obj.radius) if isinstance(obj, Ball) else 0.3
        # Place near the object's default position with a small random offset.
        x = float(np.clip(obj.x + rng.uniform(-1.0, 1.0), -4.5, 4.5))
        y = float(np.clip(obj.y + rng.uniform(-1.0, 1.0), -4.5, 4.5))
        positions.append((x, y, r))
    return positions or None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--levels", nargs="+",
        help="Specific level names to process (default: all two-ball + VT levels)",
    )
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED,
        help=f"Preferred seed (default: {DEFAULT_SEED}; falls back to 0-9 if not solvable)",
    )
    parser.add_argument(
        "--output-dir", default=OUTPUT_DIR,
        help="Output directory for webm files",
    )
    parser.add_argument(
        "--skip-existing", action="store_true",
        help="Skip levels that already have a webm file",
    )
    args = parser.parse_args()

    levels = args.levels or (TWO_BALL_LEVELS + VT_LEVELS)
    os.makedirs(args.output_dir, exist_ok=True)

    # Import oracle infrastructure (triggers oracle module registration).
    from interphyre.config import SimulationConfig
    from interphyre.validation.oracles import get_oracle, _defaults_registry

    config = SimulationConfig()

    ok, skipped, failed = 0, 0, 0
    for level_name in levels:
        output_path = os.path.join(args.output_dir, f"{level_name}.webm")

        if args.skip_existing and os.path.exists(output_path):
            print(f"[skip] {level_name}")
            skipped += 1
            continue

        print(f"[{level_name}] finding solution...")
        oracle_fn = get_oracle(level_name)
        if oracle_fn is None:
            print(f"  no oracle registered — skipping")
            failed += 1
            continue

        defaults = _defaults_registry.get(level_name, {})
        seed_used, positions = find_solution(level_name, args.seed, oracle_fn, defaults, config)

        if positions is None:
            print(f"  no solution found — recording best-effort attempt...")
            positions = _random_positions(level_name, args.seed, config)
            if positions is None:
                print(f"  could not build fallback action — skipping")
                failed += 1
                continue

        print(f"  solution found (seed {seed_used}), recording...")
        try:
            record_preview(level_name, seed_used, positions, config, output_path)
            print(f"  -> {output_path}")
            ok += 1
        except Exception as exc:
            print(f"  recording error: {exc}")
            failed += 1

    print(f"\nDone: {ok} recorded, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
