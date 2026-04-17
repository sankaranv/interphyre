"""
Baseline feature specifications and model fitting for the physics-probing study (§12.3).

Two baseline families are provided:
  - Scene+action feature vector: hand-crafted physics state encoding, used as input
    to MLP and XGBoost classifiers/regressors.
  - The baselines establish whether raw physics state (without LLM processing) is
    sufficient to predict CF outcomes at the same accuracy as the linear probes.

Object size-parameter encoding:
  Ball: (radius,)           — 1 param
  Bar:  (length, thickness) — 2 params
  Basket: (bottom_width, top_width, height) — 3 params
  All objects padded to 3 size params (max across types) with zeros for missing.
"""

from __future__ import annotations

import numpy as np

try:
    from sklearn.neural_network import MLPClassifier, MLPRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline

    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False

try:
    from xgboost import XGBClassifier, XGBRegressor

    _XGB_AVAILABLE = True
except ImportError:
    _XGB_AVAILABLE = False
    from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor

from ..config import RANDOM_STATE

# Maximum number of size parameters across all object types.
# Ball: 1, Bar: 2, Basket: 3 — pad to this width.
_MAX_SIZE_PARAMS = 3

# Per-object feature width before padding:
# (x, y, angle, *size_params_padded, dynamic_flag) = 3 + 3 + 1 = 7
_OBJECT_FEATURE_WIDTH = 3 + _MAX_SIZE_PARAMS + 1


def canonical_object_order(level_name: str) -> list[str]:
    """Return alphabetically-sorted list of object names for the level.

    Alphabetical order is used rather than insertion order to make the
    feature vector deterministic across scenes from the same level — object
    dict insertion order is not guaranteed stable across all Python versions
    and serialization paths.
    """
    from ..config import SCRATCH_SCENE_DICTS_DIR
    import os
    import json

    scene_dicts_dir = os.path.join(
        "/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre",
        SCRATCH_SCENE_DICTS_DIR,
        level_name,
    )
    # Load the first available scene dict to get the object names.
    for fname in sorted(os.listdir(scene_dicts_dir)):
        if fname.endswith(".json"):
            with open(os.path.join(scene_dicts_dir, fname)) as f:
                scene_dict = json.load(f)
            return sorted(scene_dict.keys())
    raise FileNotFoundError(f"No scene dict JSON found in {scene_dicts_dir}")


def _extract_size_params(obj_dict: dict) -> list[float]:
    """Extract per-type size parameters and pad to _MAX_SIZE_PARAMS."""
    shape = obj_dict.get("shape", "").lower()
    if shape == "ball":
        params = [float(obj_dict.get("radius", 0.0))]
    elif shape == "bar":
        params = [
            float(obj_dict.get("length", 0.0)),
            float(obj_dict.get("thickness", 0.0)),
        ]
    elif shape == "basket":
        params = [
            float(obj_dict.get("bottom_width", 0.0)),
            float(obj_dict.get("top_width", 0.0)),
            float(obj_dict.get("height", 0.0)),
        ]
    else:
        # Unknown shape: leave all size params as zero.
        params = []

    # Pad to _MAX_SIZE_PARAMS.
    padded = params + [0.0] * (_MAX_SIZE_PARAMS - len(params))
    return padded[:_MAX_SIZE_PARAMS]


def build_scene_feature_vector(
    scene_dict: dict,
    parsed_action: tuple[float, float, float],
    level_name: str,
) -> np.ndarray:
    """Build the scene+action feature vector per §12.3.

    Per-object features: (x, y, angle, *size_params_padded, dynamic_flag).
    Objects appear in canonical_object_order — alphabetical — so the feature
    index of any object is stable across all scenes from the same level.
    Append action (x, y, radius) at the end.
    Returns float32 numpy array of shape [n_objects * _OBJECT_FEATURE_WIDTH + 3].
    """
    object_names = canonical_object_order(level_name)
    feature_parts = []

    for name in object_names:
        obj = scene_dict.get(name, {})
        x = float(obj.get("x", 0.0))
        y = float(obj.get("y", 0.0))
        angle = float(obj.get("angle", 0.0))
        size_params = _extract_size_params(obj)
        dynamic_flag = float(bool(obj.get("dynamic", False)))
        feature_parts.extend([x, y, angle] + size_params + [dynamic_flag])

    # Append parsed action (x, y, radius).
    feature_parts.extend([parsed_action[0], parsed_action[1], parsed_action[2]])

    return np.array(feature_parts, dtype=np.float32)


def fit_mlp_classifier_baseline(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> object:
    """Fit MLPClassifier with StandardScaler pipeline per §12.3.

    Architecture: two hidden layers of 128 units, ReLU, Adam, max_iter=500,
    early stopping on 10% validation split.  StandardScaler is fit on
    X_train only and applied via Pipeline to prevent leakage.
    """
    if not _SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn is required for MLP baselines")

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "mlp",
                MLPClassifier(
                    hidden_layer_sizes=(128, 128),
                    activation="relu",
                    solver="adam",
                    max_iter=500,
                    early_stopping=True,
                    validation_fraction=0.1,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    pipeline.fit(X_train, y_train)
    return pipeline


def fit_xgb_classifier_baseline(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> object:
    """Fit XGBClassifier per §12.3, falling back to GradientBoostingClassifier if unavailable."""
    if _XGB_AVAILABLE:
        model = XGBClassifier(
            max_depth=5,
            n_estimators=200,
            learning_rate=0.1,
            random_state=RANDOM_STATE,
            eval_metric="logloss",
            verbosity=0,
        )
    else:
        model = GradientBoostingClassifier(
            max_depth=5,
            n_estimators=200,
            learning_rate=0.1,
            random_state=RANDOM_STATE,
        )
    model.fit(X_train, y_train)
    return model


def fit_mlp_regressor_baseline(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> object:
    """H4 regression baseline: MLPRegressor with same architecture as classifier.

    StandardScaler pipeline prevents scale sensitivity from dominating R².
    """
    if not _SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn is required for MLP baselines")

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "mlp",
                MLPRegressor(
                    hidden_layer_sizes=(128, 128),
                    activation="relu",
                    solver="adam",
                    max_iter=500,
                    early_stopping=True,
                    validation_fraction=0.1,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    pipeline.fit(X_train, y_train)
    return pipeline


def fit_xgb_regressor_baseline(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> object:
    """H4 regression baseline: XGBRegressor or GradientBoostingRegressor fallback."""
    if _XGB_AVAILABLE:
        model = XGBRegressor(
            max_depth=5,
            n_estimators=200,
            learning_rate=0.1,
            random_state=RANDOM_STATE,
            verbosity=0,
        )
    else:
        model = GradientBoostingRegressor(
            max_depth=5,
            n_estimators=200,
            learning_rate=0.1,
            random_state=RANDOM_STATE,
        )
    model.fit(X_train, y_train)
    return model
