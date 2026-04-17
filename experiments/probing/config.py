"""
Probing study configuration constants.

Physics config deviates from library defaults — see §2.3 of probing_plan.md.
warm_starting=False and continuous_physics=False maximize snapshot/restore
fidelity across matched factual/counterfactual pairs. max_steps=500 aligns
with the run_until budget used throughout the codebase.
"""

from __future__ import annotations

import numpy as np

from interphyre.config import SimulationConfig

# §2.3: Physics configuration contract — pinned for the entire probing study.
# Do not use library defaults; always pass this to env construction.
PROBING_SIM_CONFIG = SimulationConfig(
    warm_starting=False,
    continuous_physics=False,
    max_steps=500,
    enable_interventions=True,
)

# §9.7: Seed partition per level (10,001 validated seeds total per level).
CALIBRATION_SEEDS_COUNT = 200
TRAIN_SEEDS_COUNT = 3_000
EVAL_SEEDS_COUNT = 1_000
# ~5,800 seeds remain as reserve for §9.7 cascade rule.

CALIBRATION_SEED_SLICE = slice(0, 200)
TRAIN_SEED_SLICE = slice(200, 3_200)
EVAL_SEED_SLICE = slice(3_200, 4_200)

# Levels in scope for the primary study. §2.1 and §2.2 govern whether
# two_body_problem is replaced by keyhole at execution time.
PRIMARY_LEVELS = ["down_to_earth", "end_of_line", "two_body_problem"]
FALLBACK_LEVEL = "keyhole"

# §9.7: Sample-size gate — minimum conditioned instances per (level, target, direction).
MIN_CONDITIONED_INSTANCES = 150

# §9.2 and §9.7: Per-level perturbation configuration.
# Direction tuples are unit vectors in Box2D world coordinates.
# "along-surface" and "normal" are resolved per §9.2's Direction basis description.
# +x = right, +y = up. Static targets: set_position; dynamic: apply_impulse.
LEVEL_PERTURBATION_SPEC: dict[str, list[dict]] = {
    "down_to_earth": [
        {
            "target": "purple_ground",
            "role": "terminal",
            "body_type": "static",
            "primitive": "set_position",
            "directions": [(1.0, 0.0), (-1.0, 0.0)],  # ±x along-surface
        },
        {
            "target": "platform",
            "role": "intermediate",
            "body_type": "static",
            "primitive": "set_position",
            "directions": [
                (1.0, 0.0),
                (-1.0, 0.0),
                (0.0, 1.0),
                (0.0, -1.0),
            ],  # ±x along, ±y normal
        },
    ],
    "end_of_line": [
        {
            "target": "purple_wall",
            "role": "terminal",
            "body_type": "static",
            "primitive": "set_position",
            "directions": [
                (0.0, 1.0),
                (0.0, -1.0),
                (1.0, 0.0),
                (-1.0, 0.0),
            ],  # ±y along, ±x normal
        },
        {
            "target": "shelf",
            "role": "intermediate",
            "body_type": "static",
            "primitive": "set_position",
            "directions": [
                (1.0, 0.0),
                (-1.0, 0.0),
                (0.0, 1.0),
                (0.0, -1.0),
            ],  # ±x along, ±y normal
        },
    ],
    "two_body_problem": [
        {
            "target": "blue_ball",
            "role": "terminal",
            "body_type": "dynamic",
            "primitive": "apply_impulse",
            "directions": [
                (1.0, 0.0),
                (-1.0, 0.0),
                (0.0, 1.0),
                (0.0, -1.0),
            ],  # ±x, ±y at center of mass
        },
    ],
    "keyhole": [
        {
            "target": "purple_pad",
            "role": "terminal",
            "body_type": "static",
            "primitive": "set_position",
            "directions": [(1.0, 0.0), (-1.0, 0.0)],  # ±x along-surface
        },
    ],
    # Dynamic off-chain ball candidates identified during level sweep (2026-04-17).
    # Both levels share the red→green→purple_ground causal topology with a dynamic
    # ball object (blocking_ball / gray_ball) that is absent from the success condition
    # and can receive impulse perturbations without geometry-based guard rejection.
    "mind_the_gap": [
        {
            "target": "blocking_ball",
            "role": "off_chain",
            "body_type": "dynamic",
            "primitive": "apply_impulse",
            "directions": [
                (1.0, 0.0),
                (-1.0, 0.0),
                (0.0, 1.0),
                (0.0, -1.0),
            ],  # ±x, ±y impulse at center of mass
        },
    ],
    "zebra_crossing": [
        {
            "target": "gray_ball",
            "role": "off_chain",
            "body_type": "dynamic",
            "primitive": "apply_impulse",
            "directions": [
                (1.0, 0.0),
                (-1.0, 0.0),
                (0.0, 1.0),
                (0.0, -1.0),
            ],  # ±x, ±y impulse at center of mass
        },
    ],
}

# §9.4: Magnitude calibration grids.
# Impulses for dynamic targets: 0.1 to 10 kg·m/s (8 log-spaced points).
# Translations for static targets: 0.01 to 1.0 m (8 log-spaced points).
IMPULSE_MAGNITUDE_GRID = np.logspace(-1, 1, 8).tolist()  # kg·m/s
TRANSLATION_MAGNITUDE_GRID = np.logspace(-2, 0, 8).tolist()  # meters

# §9.4: CF-flip-rate band for magnitude selection.
CF_FLIP_RATE_MIN = 0.3
CF_FLIP_RATE_MAX = 0.7

# §9.2: Physical-validity guard constants.
WORLD_BOUNDS_EPSILON = 0.05  # margin inside world walls

# §11.4: HDF5 storage paths.
SCRATCH_ACTIVATIONS_DIR = "scratch/probing/activations"
SCRATCH_CF_OUTCOMES_DIR = "scratch/probing/cf_outcomes"
SCRATCH_SCENE_DICTS_DIR = "scratch/probing/scene_dicts"
RESULTS_PROBING_DIR = "results/probing"
CALIBRATION_JSON = "scratch/probing/calibration.json"

# §10.4: Primary model commitment.
PRIMARY_MODEL_ID = "Qwen/Qwen3-8B"
SECONDARY_MODEL_ID = "google/gemma-2-9b-it"

# §10.4: Sampling hyperparameters.
TEMPERATURE = 0.7
TOP_P = 0.95
# Increased from 4096: Qwen3-8B thinking mode uses ~4000 tokens for <think>...</think>
# before reaching <action>; 16384 gives ample headroom for both thinking and answer.
MAX_NEW_TOKENS = 16384

# §11.1: Qwen3-8B architecture constants (verify at load time per §14.1).
QWEN3_8B_NUM_LAYERS = 36
QWEN3_8B_HIDDEN_SIZE = 4096

# §14.2: Gemma 2 9B-IT architecture constants.
GEMMA2_9B_NUM_LAYERS = 42
GEMMA2_9B_HIDDEN_SIZE = 3584

# §11.2: T3 mean-pool window.
T3_POOL_SIZE = 32

# §12.1: Regularization grids.
LOGISTIC_C_GRID = np.logspace(-3, 3, 7).tolist()  # C ∈ {1e-3 ... 1e3}
RIDGE_ALPHA_GRID = np.logspace(-3, 3, 7).tolist()  # α ∈ {1e-3 ... 1e3}

# §12.4: Bootstrap CI settings.
BOOTSTRAP_N_RESAMPLES = 1_000
BOOTSTRAP_SEED = 42

# §12.5: BH FDR threshold.
FDR_Q = 0.05

# §15.3: Pass/fail thresholds.
H1_H3_BALANCED_ACC_THRESHOLD = 0.55  # lower CI must exceed this
H4_R2_THRESHOLD = 0.20  # lower CI on R² must exceed this
H5_TRANSFER_BALANCED_ACC_THRESHOLD = 0.55  # same as H3
H6B_SPEARMAN_RHO_THRESHOLD = 0.30  # lower CI on ρ must exceed this
H6C_COHERENCE_FRACTION_THRESHOLD = 0.80  # parseable-and-coherent fraction
H7_RELATIVE_DEPTH_OVERLAP_TOLERANCE = 0.15  # for cross-model depth alignment

# §15.3: H6a pass rule.
H6A_MIN_PASSING_ALPHAS = 6  # of 10 positive-α values
H6A_RANDOM_CONTROL_N_DRAWS = 20  # per instance per α

# §13.2: Steering α grid bounds.
ALPHA_GRID_LOWER_FACTOR = 0.1  # ×norm_Lstar
ALPHA_GRID_UPPER_FACTOR = 2.0  # ×norm_Lstar
ALPHA_GRID_N_POINTS = 10  # positive-α branch; same for negative-α

# §13.3: H6b asymmetric-exclusion caveat flag threshold.
H6B_ASYMMETRIC_EXCLUSION_MAX_DIFF = 0.20  # 20 percentage points

# §10.5: Sampling seed namespace for primary model.
# Replication uses "probing::{model_id}::" per §14.2.
PRIMARY_SAMPLING_NAMESPACE = "probing"

# §11.3: Dead-feature guard for z-score standardization.
STANDARDIZATION_MIN_STD = 1e-6

# §11.4: HDF5 audit subset fraction.
AUDIT_FRACTION = 0.05

# §11.4: HDF5 compression.
HDF5_COMPRESSION = "gzip"
HDF5_COMPRESSION_OPTS = 4

# §9.5: H4 per-level target-object mapping (factual rollout first contact).
H4_TARGET_OBJECT: dict[str, str] = {
    "down_to_earth": "purple_ground",
    "end_of_line": "purple_wall",
    "two_body_problem": "blue_ball",
    "keyhole": "purple_pad",
}

# §2.2: two_body_problem filter retention fallback trigger.
TWO_BODY_MIN_FILTER_RETENTION = 0.30

# Random state for sklearn operations — propagates to all splits, CV folds,
# MLP initializations per §12.2.
RANDOM_STATE = 42

# §12.2: Train/eval inner split.
INNER_EVAL_FRACTION = 0.20
