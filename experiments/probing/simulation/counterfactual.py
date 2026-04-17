"""
Counterfactual outcome generator for the probing study (§9.2, §9.4).

Used during dataset construction (train/eval phases) after calibration has
committed a single magnitude per (level, target, direction). Each call to
generate_cf_outcome applies one perturbation from a branch snapshot and
returns the binary CF outcome and perturbation metadata.

Direction keys in calibration.json use the convention f"{dx:+.1f},{dy:+.1f}"
so they survive JSON round-trips; the same convention is used here.
"""

from __future__ import annotations

import logging
import time

from interphyre.interventions.triggers import on_success

from ..config import LEVEL_PERTURBATION_SPEC
from .guards import validate_static_perturbation

logger = logging.getLogger(__name__)

# Direction key format shared with calibration.py and downstream readers.
_DIRECTION_KEY_FMT = "{:+.1f},{:+.1f}"


def _direction_key(direction: tuple[float, float]) -> str:
    return _DIRECTION_KEY_FMT.format(direction[0], direction[1])


def generate_cf_outcome(
    env,
    snapshot,
    target_name: str,
    direction: tuple[float, float],
    magnitude: float,
    primitive: str,
    scene_dict: dict,
    neighbor_surface_vectors: list[tuple[float, float]],
) -> dict:
    """Apply one perturbation from snapshot and roll forward.

    Restores env to snapshot, applies the perturbation (set_position or
    apply_impulse), then runs to max_steps=500 under the success trigger.

    Returns a dict with keys:
      cf_outcome (bool | None): True=success, None=invalid perturbation
      cf_rollout_seconds (float): wall-clock seconds for the CF rollout
      perturbation_validity (str): "valid", "no_intersect_fail",
          "out_of_bounds", or "surface_tangent"
    """
    env.restore(snapshot)

    if primitive == "set_position":
        target_obj = scene_dict["objects"].get(target_name)
        if target_obj is None:
            return {
                "cf_outcome": None,
                "cf_rollout_seconds": 0.0,
                "perturbation_validity": "no_intersect_fail",
            }

        new_x = target_obj["x"] + direction[0] * magnitude
        new_y = target_obj["y"] + direction[1] * magnitude

        valid, reason = validate_static_perturbation(
            target_name,
            new_x,
            new_y,
            scene_dict,
            neighbor_surface_vectors,
            direction,
        )
        if not valid:
            return {
                "cf_outcome": None,
                "cf_rollout_seconds": 0.0,
                "perturbation_validity": reason,
            }

        env.set_position(target_name, x=new_x, y=new_y)

    elif primitive == "apply_impulse":
        impulse = (direction[0] * magnitude, direction[1] * magnitude)
        env.apply_impulse(target_name, impulse)

    else:
        raise ValueError(f"Unknown primitive: {primitive!r}")

    t0 = time.perf_counter()
    success_trigger = on_success()
    env.run_until(success_trigger, max_steps=500)
    cf_success = env._level.success_condition(env.engine)
    elapsed = time.perf_counter() - t0

    return {
        "cf_outcome": cf_success,
        "cf_rollout_seconds": elapsed,
        "perturbation_validity": "valid",
    }


def generate_all_cf_outcomes_for_instance(
    env,
    instance_id: str,
    level_name: str,
    calibration_data: dict,
    factual_outcome: bool,
    branch_snapshot,
    scene_dict: dict,
) -> list[dict]:
    """Generate CF outcomes for all (target, direction) combos of one instance.

    Reads committed magnitudes from calibration_data (the parsed contents of
    CALIBRATION_JSON). Skips (target, direction) combos for which calibration
    returned None (dropped directions per §9.4 selection rule).

    Returns a list of row dicts with columns:
      instance_id, target, direction, magnitude, cf_outcome,
      cf_rollout_seconds, perturbation_validity

    Neighbor surface vectors are not pre-computed globally; they are passed
    as an empty list because the surface-tangent guard is primarily useful
    during calibration's direction-selection pre-flight. At training/eval time
    the directions are already committed from LEVEL_PERTURBATION_SPEC.
    """
    level_cal = calibration_data.get(level_name, {})
    spec_entries = LEVEL_PERTURBATION_SPEC.get(level_name, [])

    rows: list[dict] = []
    for entry in spec_entries:
        target = entry["target"]
        primitive = entry["primitive"]
        directions = entry["directions"]
        target_cal = level_cal.get(target, {})

        for direction in directions:
            dk = _direction_key(direction)
            cal_result = target_cal.get(dk)
            if cal_result is None:
                # This direction was dropped during calibration; skip.
                logger.debug(
                    "Skipping %s/%s/%s for instance %s — no calibrated magnitude",
                    level_name,
                    target,
                    dk,
                    instance_id,
                )
                continue

            magnitude = cal_result["chosen_magnitude"]

            # Neighbor surface vectors are not stored per-instance; pass empty
            # list so guard (3) is a no-op here. Guard (1) and (2) still run.
            result = generate_cf_outcome(
                env=env,
                snapshot=branch_snapshot,
                target_name=target,
                direction=direction,
                magnitude=magnitude,
                primitive=primitive,
                scene_dict=scene_dict,
                neighbor_surface_vectors=[],
            )

            rows.append(
                {
                    "instance_id": instance_id,
                    "target": target,
                    "direction": dk,
                    "magnitude": magnitude,
                    "cf_outcome": result["cf_outcome"],
                    "cf_rollout_seconds": result["cf_rollout_seconds"],
                    "perturbation_validity": result["perturbation_validity"],
                }
            )

    return rows
