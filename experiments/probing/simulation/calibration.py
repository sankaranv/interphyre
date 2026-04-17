"""
Magnitude calibration for §9.4 of the probing study.

For each (level, target, direction) triple, a single perturbation magnitude
is committed before any probe training. The calibration runs on 200 seeds
disjoint from train/eval (CALIBRATION_SEED_SLICE) and selects the smallest
magnitude whose CF-flip rate falls in [CF_FLIP_RATE_MIN, CF_FLIP_RATE_MAX].

The calibration output is written to CALIBRATION_JSON and read by downstream
dataset-construction steps — it is never recomputed at training time.

Design choices that affect experimental validity:
- Branch trigger is on_contact("red_ball", "green_ball"), matching §9.1.
  Snapshotting at first red→green contact ensures the branch point is
  mechanically meaningful for all three levels in scope.
- Factual outcome is measured from the branch snapshot forward under the
  pinned physics config (PROBING_SIM_CONFIG). This makes CF-flip rate
  conditional on a fixed branch state, not on the pre-branch trajectory.
- Guard rejections are excluded from the magnitude's denominator so that
  flip-rate estimates are not diluted by geometrically infeasible samples.
- The smallest in-band magnitude is preferred to minimize scene disruption
  (§9.4 selection rule).
"""

from __future__ import annotations

import json
import logging
import os

from interphyre.interventions.triggers import on_contact, on_success
from interphyre.validation import load_valid_level

from ..config import (
    CALIBRATION_JSON,
    CF_FLIP_RATE_MAX,
    CF_FLIP_RATE_MIN,
    IMPULSE_MAGNITUDE_GRID,
    LEVEL_PERTURBATION_SPEC,
    PROBING_SIM_CONFIG,
    TRANSLATION_MAGNITUDE_GRID,
)
from .guards import validate_static_perturbation

logger = logging.getLogger(__name__)


def run_branch_and_cf_rollout(
    env,
    target_name: str,
    direction: tuple[float, float],
    magnitude: float,
    primitive: str,
    neighbor_surface_vectors: list[tuple[float, float]],
) -> str | None:
    """Run branch trigger, apply perturbation, roll forward; return outcome string.

    Returns one of:
      "success"             — CF rollout reached success condition
      "failure"             — CF rollout exhausted max_steps without success
      "branch_never_fired"  — red_ball never contacted green_ball within budget
      "perturbation_invalid"— §9.2 guard rejected the perturbation

    The branch trigger is on_contact("red_ball", "green_ball") per §9.1.
    Snapshot is captured at first contact; factual outcome is measured from
    the same snapshot. CF perturbation is applied after restoring the snapshot
    so that factual and CF rollouts share an identical branch state.
    """

    branch_trigger = on_contact("red_ball", "green_ball")
    snapshot, _step = env.run_until(branch_trigger, max_steps=500)

    if snapshot is None:
        return "branch_never_fired"

    # Apply perturbation from the branch snapshot.
    env.restore(snapshot)

    if primitive == "set_position":
        scene_dict = env.describe_scene()
        target_obj = scene_dict["objects"].get(target_name)
        if target_obj is None:
            return "perturbation_invalid"

        new_x = target_obj["x"] + direction[0] * magnitude
        new_y = target_obj["y"] + direction[1] * magnitude

        valid, _reason = validate_static_perturbation(
            target_name,
            new_x,
            new_y,
            scene_dict,
            neighbor_surface_vectors,
            direction,
        )
        if not valid:
            return "perturbation_invalid"

        env.set_position(target_name, x=new_x, y=new_y)

    elif primitive == "apply_impulse":
        # Dynamic targets: apply impulse as (direction * magnitude).
        # No position-based guards — post-impulse overlap is resolved by Box2D.
        impulse = (direction[0] * magnitude, direction[1] * magnitude)
        env.apply_impulse(target_name, impulse)

    else:
        raise ValueError(f"Unknown primitive: {primitive!r}")

    # Roll forward to measure CF outcome.
    success_trigger = on_success()
    _snap, _final_step = env.run_until(success_trigger, max_steps=500)
    cf_success = env.describe_scene()["success"] or (
        env._level.success_condition(env.engine)
    )

    return "success" if cf_success else "failure"


def _run_factual_from_snapshot(env, snapshot) -> bool:
    """Roll forward from snapshot without perturbation; return factual success."""
    env.restore(snapshot)
    success_trigger = on_success()
    env.run_until(success_trigger, max_steps=500)
    return env._level.success_condition(env.engine)


def compute_cf_flip_rate(
    factual_outcomes: list[bool],
    cf_outcomes: list[str],
) -> float:
    """Return the fraction of instances where CF outcome disagrees with factual.

    Only "success" and "failure" CF outcomes contribute; "branch_never_fired"
    and "perturbation_invalid" are excluded from the denominator.
    """
    n_valid = 0
    n_flip = 0
    for factual, cf in zip(factual_outcomes, cf_outcomes):
        if cf not in ("success", "failure"):
            continue
        n_valid += 1
        cf_bool = cf == "success"
        if cf_bool != factual:
            n_flip += 1
    if n_valid == 0:
        return float("nan")
    return n_flip / n_valid


def select_calibration_magnitude(
    level_name: str,
    target_name: str,
    direction: tuple[float, float],
    primitive: str,
    seeds: list[int],
    neighbor_surface_vectors: list[tuple[float, float]],
) -> dict | None:
    """Run calibration for one (level, target, direction); return chosen magnitude.

    Returns a dict with keys:
      chosen_magnitude, cf_flip_rate, guard_rejection_count, n_valid_seeds
    or None if no grid point lands in [CF_FLIP_RATE_MIN, CF_FLIP_RATE_MAX].

    Iterates the magnitude grid from smallest to largest and returns the first
    in-band point, minimising scene disruption per §9.4's selection rule.
    """
    grid = (
        IMPULSE_MAGNITUDE_GRID
        if primitive == "apply_impulse"
        else TRANSLATION_MAGNITUDE_GRID
    )

    for magnitude in sorted(grid):
        factual_outcomes: list[bool] = []
        cf_outcomes: list[str] = []
        guard_rejections = 0

        for seed in seeds:
            try:
                validated = load_valid_level(
                    level_name, seed=seed, config=PROBING_SIM_CONFIG
                )
            except RuntimeError:
                logger.debug(
                    "Skipping seed=%d for %s — no valid variant found", seed, level_name
                )
                continue

            # Build env from the validated level object directly to avoid re-running
            # the oracle; pass the pre-built Level so env uses the same geometry.
            from interphyre.environment import InterphyreEnv

            env = InterphyreEnv(
                validated.level,
                config=PROBING_SIM_CONFIG,
                enable_interventions=True,
            )
            env.reset()

            # Place the oracle red_ball so the branch trigger can fire.
            # Without this call red_ball sits at its dummy initial position
            # and on_contact("red_ball", "green_ball") never fires.
            rb = validated.scene_dict["red_ball"]
            env.place_action((rb["x"], rb["y"], rb["radius"]))

            # Obtain branch snapshot first (needed for both factual and CF).
            from interphyre.interventions.triggers import on_contact as _on_contact

            branch_trigger = _on_contact("red_ball", "green_ball")
            snapshot, _step = env.run_until(branch_trigger, max_steps=500)

            if snapshot is None:
                cf_outcomes.append("branch_never_fired")
                factual_outcomes.append(False)
                continue

            # Measure factual outcome from branch snapshot.
            factual = _run_factual_from_snapshot(env, snapshot)
            factual_outcomes.append(factual)

            # Restore to branch and run CF rollout.
            env.restore(snapshot)

            if primitive == "set_position":
                scene_dict = env.describe_scene()
                target_obj = scene_dict["objects"].get(target_name)
                if target_obj is None:
                    cf_outcomes.append("perturbation_invalid")
                    guard_rejections += 1
                    continue

                new_x = target_obj["x"] + direction[0] * magnitude
                new_y = target_obj["y"] + direction[1] * magnitude

                valid, _reason = validate_static_perturbation(
                    target_name,
                    new_x,
                    new_y,
                    scene_dict,
                    neighbor_surface_vectors,
                    direction,
                )
                if not valid:
                    cf_outcomes.append("perturbation_invalid")
                    guard_rejections += 1
                    continue

                env.set_position(target_name, x=new_x, y=new_y)

            elif primitive == "apply_impulse":
                impulse = (direction[0] * magnitude, direction[1] * magnitude)
                env.apply_impulse(target_name, impulse)

            from interphyre.interventions.triggers import on_success as _on_success

            success_trigger = _on_success()
            env.run_until(success_trigger, max_steps=500)
            cf_success = env._level.success_condition(env.engine)
            cf_outcomes.append("success" if cf_success else "failure")

        flip_rate = compute_cf_flip_rate(factual_outcomes, cf_outcomes)
        n_valid = sum(1 for o in cf_outcomes if o in ("success", "failure"))

        logger.info(
            "Calibration %s/%s %s mag=%.4f flip_rate=%.3f n_valid=%d rejections=%d",
            level_name,
            target_name,
            direction,
            magnitude,
            flip_rate if flip_rate == flip_rate else -1,
            n_valid,
            guard_rejections,
        )

        if (
            not (flip_rate != flip_rate)
            and CF_FLIP_RATE_MIN <= flip_rate <= CF_FLIP_RATE_MAX
        ):
            return {
                "chosen_magnitude": magnitude,
                "cf_flip_rate": flip_rate,
                "guard_rejection_count": guard_rejections,
                "n_valid_seeds": n_valid,
            }

    return None


def measure_oracle_success_rate(level_name: str, seed_indices: list[int]) -> float:
    """Run oracle actions on calibration seeds and return factual success rate.

    Places each seed's known-correct action (from validated.scene_dict["red_ball"]),
    runs the full simulation to on_success or max_steps, and returns the fraction
    of seeds that succeed. This is independent of perturbations and gives a baseline
    for what success rate is achievable given perfect placement.

    Logged at INFO level so the number appears in the SLURM calibration job log
    alongside flip-rate diagnostics.
    """
    from interphyre.environment import InterphyreEnv
    from interphyre.interventions.triggers import on_success as _on_success

    n_success = 0
    n_valid = 0
    for seed in seed_indices:
        try:
            validated = load_valid_level(level_name, seed=seed, config=PROBING_SIM_CONFIG)
        except RuntimeError:
            continue
        rb = validated.scene_dict.get("red_ball")
        if rb is None:
            continue
        env = InterphyreEnv(validated.level, config=PROBING_SIM_CONFIG, enable_interventions=True)
        env.reset()
        try:
            env.place_action((rb["x"], rb["y"], rb["radius"]))
        except Exception:
            continue
        env.run_until(_on_success(), max_steps=500)
        n_valid += 1
        if env._level.success_condition(env.engine):
            n_success += 1

    rate = n_success / n_valid if n_valid > 0 else float("nan")
    logger.info(
        "Oracle success rate for %s: %d/%d = %.1f%%", level_name, n_success, n_valid, rate * 100
    )
    return rate


def run_calibration_for_level(
    level_name: str,
    seed_indices: list[int],
    calibration_json_path: str | None = None,
) -> dict:
    """Run calibration for all (target, direction) combinations of a level.

    Returns nested dict: {target_name: {direction_key: calibration_result}}.
    Writes the result to calibration_json_path (or CALIBRATION_JSON if not
    provided), merging with any existing entries so that re-runs for
    individual levels do not clobber other levels.

    Direction keys follow the convention f"{dx:+.1f},{dy:+.1f}" so they
    survive JSON round-trips without ambiguity.
    """
    measure_oracle_success_rate(level_name, seed_indices)
    spec_entries = LEVEL_PERTURBATION_SPEC.get(level_name, [])
    level_results: dict[str, dict] = {}

    for entry in spec_entries:
        target = entry["target"]
        primitive = entry["primitive"]
        directions = entry["directions"]
        # Neighbor surface vectors are not pre-computed here; they depend on
        # the scene geometry, which varies per seed. The guard is still applied
        # per-instance inside select_calibration_magnitude using an empty list
        # (no surface-tangent rejection during calibration itself — the
        # directions in LEVEL_PERTURBATION_SPEC are pre-validated by design).
        # Surface-tangent guard is the responsibility of the run-time CF
        # generator in counterfactual.py where per-instance geometry is known.
        neighbor_surface_vectors: list[tuple[float, float]] = []

        target_results: dict[str, dict | None] = {}
        for direction in directions:
            direction_key = f"{direction[0]:+.1f},{direction[1]:+.1f}"
            result = select_calibration_magnitude(
                level_name=level_name,
                target_name=target,
                direction=direction,
                primitive=primitive,
                seeds=seed_indices,
                neighbor_surface_vectors=neighbor_surface_vectors,
            )
            if result is None:
                logger.warning(
                    "No in-band magnitude for %s/%s/%s — this (target, direction) "
                    "will be dropped from probing",
                    level_name,
                    target,
                    direction_key,
                )
            target_results[direction_key] = result

        level_results[target] = target_results

    # Merge into the target JSON atomically: read → update → write.
    output_path = calibration_json_path or CALIBRATION_JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    existing: dict = {}
    if os.path.exists(output_path):
        with open(output_path) as fh:
            content = fh.read().strip()
            if content:
                existing = json.loads(content)

    existing[level_name] = level_results
    with open(output_path, "w") as fh:
        json.dump(existing, fh, indent=2)

    logger.info("Calibration written to %s", output_path)
    return level_results
