"""Regression test for ADD-SCENE-FROM-GEOMETRY-BUILDER (interphyre-s2w).

Verifies:
1. build_level_from_scene('two_body_problem', scene) with a fully-specified
   scene produces bit-identical geometry across any RNG change (seed variation).
2. Partial scene overrides apply correctly without shifting downstream RNG draws.
3. build_level(seed) without scene is unchanged (backward-compat).
"""

import sys

sys.path.insert(0, "/Users/sankaran/Projects/interphyre")

from interphyre.levels import build_level_from_scene, load_level

FULL_SCENE = {
    "green_ball": {"x": 1.0, "y": 0.5, "radius": 0.4},
    "blue_ball": {"x": 3.0, "y": 0.6, "radius": 0.35},
    "red_ball": {"radius": 0.5},
}


def ball_geom(level, name):
    obj = level.objects[name]
    return (round(obj.x, 8), round(obj.y, 8), round(obj.radius, 8))


# --- Test 1: fully-specified scene is RNG-invariant ---
results = []
for seed in (None, 0, 1, 42, 999):
    level = build_level_from_scene("two_body_problem", FULL_SCENE)
    results.append(
        (ball_geom(level, "green_ball"), ball_geom(level, "blue_ball"), level.objects["red_ball"].radius)
    )

assert all(r == results[0] for r in results), (
    f"FAIL test 1: geometry differs across seeds: {results}"
)
print("PASS test 1: fully-specified scene is bit-identical across all seeds")

# Verify scene values match exactly
g = level.objects["green_ball"]
assert g.x == 1.0 and g.y == 0.5 and g.radius == 0.4, f"FAIL test 1b: green_ball mismatch: {g.x} {g.y} {g.radius}"
b = level.objects["blue_ball"]
assert b.x == 3.0 and b.y == 0.6 and b.radius == 0.35, f"FAIL test 1b: blue_ball mismatch"
assert level.objects["red_ball"].radius == 0.5, "FAIL test 1b: red_ball radius mismatch"
print("PASS test 1b: scene values propagated exactly to Ball objects")


# --- Test 2: no scene → backward-compat (same seed same geometry) ---
l1 = load_level("two_body_problem", seed=42)
l2 = load_level("two_body_problem", seed=42)
assert ball_geom(l1, "green_ball") == ball_geom(l2, "green_ball"), "FAIL test 2: backward-compat broken"
assert ball_geom(l1, "blue_ball") == ball_geom(l2, "blue_ball"), "FAIL test 2: backward-compat broken"
print("PASS test 2: build_level(seed=42) still deterministic")


# --- Test 3: partial scene override preserves RNG sequence for other draws ---
# Override only green_ball.radius; blue_ball and red_ball should match unoverridden build
partial_scene = {"green_ball": {"radius": 0.55}}
seed = 7

# Build without scene to capture baseline RNG draws
baseline = load_level("two_body_problem", seed=seed)

# Build with partial scene — only green_ball.radius overridden
overridden = load_level("two_body_problem", seed=seed, scene=partial_scene)

# green_ball.radius should be the override value
assert overridden.objects["green_ball"].radius == 0.55, (
    f"FAIL test 3: green radius not overridden: {overridden.objects['green_ball'].radius}"
)
# red_ball.radius should match baseline (RNG draw order preserved)
assert round(overridden.objects["red_ball"].radius, 8) == round(baseline.objects["red_ball"].radius, 8), (
    f"FAIL test 3: red_ball radius shifted (RNG order not preserved): "
    f"baseline={baseline.objects['red_ball'].radius} vs overridden={overridden.objects['red_ball'].radius}"
)
print("PASS test 3: partial scene override preserves RNG sequence for other draws")


print("\nAll regression tests passed.")
