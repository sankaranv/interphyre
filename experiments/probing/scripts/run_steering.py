"""
Entry point for §13 steering protocol (H6a/H6b/H6c).

Requires H3 probes to be trained (L*, p*, DIM direction per (level, target, direction)).
Runs steered inference, computes behavioral-change metrics, physics-consistency,
and coherence metrics. Writes results to results/probing/.

Usage:
    python -m experiments.probing.scripts.run_steering \
        --model-id Qwen/Qwen3-8B \
        --level down_to_earth \
        --target purple_ground \
        --direction-key "+1.0,+0.0"

GPU required. Run via SLURM.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run H6 steering for one (level, target, direction).")
    parser.add_argument("--model-id", default="Qwen/Qwen3-8B")
    parser.add_argument("--level", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--direction-key", required=True, help="e.g. '+1.0,+0.0'")
    parser.add_argument("--calibration-json", default="scratch/probing/calibration.json")
    parser.add_argument("--h3-results-dir", default="results/probing")
    parser.add_argument("--activations-dir", default="scratch/probing/activations")
    parser.add_argument("--cf-outcomes-dir", default="scratch/probing/cf_outcomes")
    parser.add_argument("--scene-dicts-dir", default="scratch/probing/scene_dicts")
    parser.add_argument("--output-dir", default="results/probing")
    parser.add_argument("--n-eval-instances", type=int, default=200,
                        help="Number of eval instances to run steered inference on.")
    args = parser.parse_args()

    import numpy as np
    from experiments.probing.config import PROBING_SIM_CONFIG, H4_TARGET_OBJECT
    from experiments.probing.steering.direction import (
        build_alpha_grid,
        compute_norm_Lstar,
    )
    from experiments.probing.steering.injection import run_steered_inference
    from experiments.probing.steering.behavioral import (
        action_tuple_distance,
        cot_edit_distance,
        random_controls_for,
        compute_h6a_result,
    )
    from experiments.probing.steering.physics import (
        compute_delta_cf_flip_rate,
        compute_h6b_spearman_rho,
        h6b_bootstrap_ci,
    )
    from experiments.probing.steering.coherence import (
        compute_parseable_fraction,
        h6c_passes,
    )
    from experiments.probing.inference.runner import load_model_and_tokenizer
    from experiments.probing.inference.prompts import render_prompt
    from experiments.probing.simulation.counterfactual import generate_all_cf_outcomes_for_instance
    from interphyre.validation import load_valid_level
    from interphyre.interventions.triggers import on_contact

    # Load calibration data.
    with open(args.calibration_json) as f:
        calib = json.load(f)

    steering_info = calib.get(args.level, {}).get(args.target, {}).get(
        args.direction_key, {}
    ).get("steering", {})

    if not steering_info:
        logger.error(
            "No steering info found for %s/%s/%s in calibration.json. "
            "Run probe training first to populate DIM directions.",
            args.level, args.target, args.direction_key,
        )
        sys.exit(1)

    dim_direction = np.array(steering_info["dim_direction"], dtype=np.float32)
    norm_Lstar = float(steering_info["norm_Lstar"])
    L_star = int(steering_info["L_star"])
    alpha_grid = np.array(steering_info["alpha_grid"])

    logger.info(
        "Steering: level=%s target=%s dir=%s L*=%d norm=%.3f",
        args.level, args.target, args.direction_key, L_star, norm_Lstar,
    )

    # Load model.
    model, tokenizer = load_model_and_tokenizer(args.model_id)

    # Load eval metadata to get instances.
    import pandas as pd
    safe_model = args.model_id.replace("/", "_")
    meta_path = Path(args.activations_dir) / f"{safe_model}_metadata.parquet"
    if not meta_path.exists():
        logger.error("Metadata parquet not found: %s", meta_path)
        sys.exit(1)

    meta_df = pd.read_parquet(str(meta_path))
    eval_instances = meta_df[
        (meta_df["level_name"] == args.level) & (meta_df["factual_outcome"])
    ].head(args.n_eval_instances)

    logger.info("Running steered inference on %d instances.", len(eval_instances))

    # Collect per-alpha results.
    alpha_steered_l2: dict[float, list] = {float(a): [] for a in alpha_grid}
    alpha_steered_cot: dict[float, list] = {float(a): [] for a in alpha_grid}
    alpha_random_l2: dict[float, list] = {float(a): [] for a in alpha_grid}
    alpha_random_cot: dict[float, list] = {float(a): [] for a in alpha_grid}
    alpha_delta_cf: dict[float, list] = {float(a): [] for a in alpha_grid}
    alpha_coherent_counts: dict[float, int] = {float(a): 0 for a in alpha_grid}

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for _, row in eval_instances.iterrows():
        iid = row["instance_id"]
        seed = int(row["seed"])
        samp_seed = int(row["sampling_seed"])

        # Load scene_dict.
        scene_dict_path = row.get("scene_dict_path")
        if not scene_dict_path or not Path(scene_dict_path).exists():
            continue
        with open(scene_dict_path) as f:
            scene_dict = json.load(f)

        # Unsteered baseline.
        unsteered_result = run_steered_inference(
            model, tokenizer, args.model_id,
            render_prompt(scene_dict, args.level),
            dim_direction, alpha=0.0, L_star=L_star, sampling_seed=samp_seed,
        )

        # Unsteered CF-flip rate (factual action, CF battery from §9.2).
        try:
            _, env = load_valid_level(args.level, seed=seed, variant=0, config=PROBING_SIM_CONFIG)
            env.reset()
            if unsteered_result["parsed_action"]:
                env.place_action(unsteered_result["parsed_action"])
            trigger = on_contact("red_ball", "green_ball")
            snapshot_u, _ = env.run_until(trigger, max_steps=500)
            unsteered_cf_rows = generate_all_cf_outcomes_for_instance(
                env, iid, args.level, args.calibration_json,
                bool(row["factual_outcome"]), snapshot_u, scene_dict,
            )
            valid_cf = [r for r in unsteered_cf_rows if r["perturbation_validity"] == "valid"]
            unsteered_flip_rate = (
                sum(1 for r in valid_cf if r["cf_outcome"] != bool(row["factual_outcome"]))
                / max(1, len(valid_cf))
            )
        except Exception as exc:
            logger.warning("Unsteered CF failed for %s: %s", iid, exc)
            continue

        for alpha in alpha_grid:
            a = float(alpha)
            steered_result = run_steered_inference(
                model, tokenizer, args.model_id,
                render_prompt(scene_dict, args.level),
                dim_direction, alpha=a, L_star=L_star, sampling_seed=samp_seed,
            )

            # H6a: behavioral change.
            l2_dist = action_tuple_distance(
                steered_result["parsed_action"], unsteered_result["parsed_action"]
            )
            cot_dist = cot_edit_distance(
                steered_result.get("output_text", ""),
                unsteered_result.get("output_text", ""),
            )
            if l2_dist is not None:
                alpha_steered_l2[a].append(l2_dist)
            if cot_dist is not None:
                alpha_steered_cot[a].append(cot_dist)

            # Random controls for H6a.
            rand_dirs = random_controls_for(iid, a, len(dim_direction))
            for rand_dir in rand_dirs:
                r_result = run_steered_inference(
                    model, tokenizer, args.model_id,
                    render_prompt(scene_dict, args.level),
                    rand_dir, alpha=1.0, L_star=L_star, sampling_seed=samp_seed,
                )
                r_l2 = action_tuple_distance(r_result["parsed_action"], unsteered_result["parsed_action"])
                r_cot = cot_edit_distance(r_result.get("output_text",""), unsteered_result.get("output_text",""))
                if r_l2 is not None:
                    alpha_random_l2[a].append(r_l2)
                if r_cot is not None:
                    alpha_random_cot[a].append(r_cot)

            # H6b: physics consistency.
            if steered_result["parsed_action"] and a != 0.0:
                try:
                    _, env_s = load_valid_level(args.level, seed=seed, variant=0, config=PROBING_SIM_CONFIG)
                    env_s.reset()
                    env_s.place_action(steered_result["parsed_action"])
                    trigger_s = on_contact("red_ball", "green_ball")
                    snap_s, _ = env_s.run_until(trigger_s, max_steps=500)
                    steered_cf_rows = generate_all_cf_outcomes_for_instance(
                        env_s, iid, args.level, args.calibration_json,
                        bool(row["factual_outcome"]), snap_s, scene_dict,
                    )
                    valid_s = [r for r in steered_cf_rows if r["perturbation_validity"] == "valid"]
                    steered_flip_rate = (
                        sum(1 for r in valid_s if r["cf_outcome"] != bool(row["factual_outcome"]))
                        / max(1, len(valid_s))
                    )
                    delta = compute_delta_cf_flip_rate(steered_flip_rate, unsteered_flip_rate)
                    alpha_delta_cf[a].append(delta)
                except Exception as exc:
                    logger.debug("Steered CF failed for %s alpha=%.3f: %s", iid, a, exc)

    # Compute H6a results.
    h6a_l2 = compute_h6a_result(alpha_steered_l2, alpha_random_l2, "action_tuple_l2")
    h6a_cot = compute_h6a_result(alpha_steered_cot, alpha_random_cot, "cot_edit")

    # Compute H6b results.
    mean_delta = [np.mean(alpha_delta_cf[float(a)]) if alpha_delta_cf[float(a)] else 0.0 for a in alpha_grid]
    rho, pval = compute_h6b_spearman_rho(alpha_grid, mean_delta)
    rho_ci = h6b_bootstrap_ci(alpha_grid, alpha_delta_cf)

    results = {
        "level": args.level,
        "target": args.target,
        "direction_key": args.direction_key,
        "L_star": L_star,
        "h6a_l2": h6a_l2,
        "h6a_cot": h6a_cot,
        "h6b_spearman_rho": rho,
        "h6b_pvalue": pval,
        "h6b_ci": list(rho_ci),
        "h6b_pass": rho > 0 and rho_ci[0] > 0.3,
        "alpha_grid": list(alpha_grid),
        "mean_delta_per_alpha": mean_delta,
    }

    safe_dir = args.direction_key.replace(",", "_").replace("+", "p").replace("-", "n")
    out_path = output_dir / f"h6_{args.level}_{args.target}_{safe_dir}.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(
        "H6 results: rho=%.3f CI=(%s), H6b pass=%s. Written to %s",
        rho, rho_ci, results["h6b_pass"], out_path,
    )


if __name__ == "__main__":
    main()
