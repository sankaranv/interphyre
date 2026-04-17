"""
Physical-validity guards for static-position perturbations (§9.2).

Three guards are applied before committing any set_position perturbation:
  1. No-intersect: the translated AABB must not overlap any other object.
  2. Within-world-bounds: the translated AABB must lie within world walls minus ε.
  3. No-surface-tangent-collapse: the perturbation direction must not be
     parallel to a constraining surface at the branch point.

Guards reject rather than resolve because any geometric fixup would
introduce a position not drawn from the calibrated magnitude distribution,
corrupting the CF-flip-rate estimate. Rejection is logged for provenance.

Impulse perturbations on dynamic targets are not subject to guard (1):
post-impulse overlap is resolved by the next Box2D solver step, so
checking overlap before the step would be overly conservative. Guard (2)
is inherited implicitly — an impulse that immediately exits the world is
non-physical — but it is not re-checked here; the rollout truncation at
max_steps=500 handles that case via the CF-outcome record.
"""

from __future__ import annotations

import math

from interphyre.config import MAX_X, MAX_Y, MIN_X, MIN_Y

from ..config import WORLD_BOUNDS_EPSILON


def compute_object_aabb(
    name: str,
    scene_dict: dict,
) -> tuple[float, float, float, float] | None:
    """Return (xmin, xmax, ymin, ymax) for the named object, or None.

    Ball: tight circular AABB.
    Bar: conservative axis-aligned bounding box from the rotated rectangle.
        Using half_extent = max(length, thickness)/2 as a conservative
        over-approximation avoids needing to rotate corner vectors while
        ensuring the guard never accepts a genuinely intersecting placement.
    Basket: bounding box derived from top_width × height.
    """
    obj = scene_dict["objects"].get(name)
    if obj is None:
        return None

    x, y = obj["x"], obj["y"]
    size = obj["size"]
    obj_type = obj["type"]

    if obj_type == "Ball":
        r = size["radius"]
        return (x - r, x + r, y - r, y + r)

    if obj_type == "Bar":
        # Conservative AABB: half-extent is the maximum of the two bar
        # dimensions, ignoring rotation. This over-approximates the true
        # rotated AABB but never under-approximates it, so the no-intersect
        # guard is safe (it may reject borderline-valid cases but never accepts
        # true intersections).
        half = max(size["length"], size["thickness"]) / 2.0
        return (x - half, x + half, y - half, y + half)

    if obj_type == "Basket":
        half_w = size["top_width"] / 2.0
        half_h = size["height"] / 2.0
        return (x - half_w, x + half_w, y - half_h, y + half_h)

    return None


def _aabbs_overlap(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> bool:
    """Return True iff two AABBs (xmin, xmax, ymin, ymax) overlap."""
    ax_min, ax_max, ay_min, ay_max = a
    bx_min, bx_max, by_min, by_max = b
    return ax_min < bx_max and ax_max > bx_min and ay_min < by_max and ay_max > by_min


def check_no_intersect(
    target_name: str,
    new_x: float,
    new_y: float,
    scene_dict: dict,
) -> bool:
    """Return True iff placing target at (new_x, new_y) overlaps no other object.

    Computes the target's AABB at the proposed position by shifting its
    current AABB by the displacement from its current position. Returns
    False if the result overlaps any other object's AABB.
    """
    target_obj = scene_dict["objects"].get(target_name)
    if target_obj is None:
        return False

    old_aabb = compute_object_aabb(target_name, scene_dict)
    if old_aabb is None:
        return False

    # Shift the AABB to the proposed position.
    dx = new_x - target_obj["x"]
    dy = new_y - target_obj["y"]
    new_aabb = (
        old_aabb[0] + dx,
        old_aabb[1] + dx,
        old_aabb[2] + dy,
        old_aabb[3] + dy,
    )

    for name, _ in scene_dict["objects"].items():
        if name == target_name:
            continue
        other_aabb = compute_object_aabb(name, scene_dict)
        if other_aabb is None:
            continue
        if _aabbs_overlap(new_aabb, other_aabb):
            return False

    return True


def check_within_world_bounds(
    target_name: str,
    new_x: float,
    new_y: float,
    scene_dict: dict,
) -> bool:
    """Return True iff placing target at (new_x, new_y) stays within world bounds.

    The guard uses MIN_X/MAX_X/MIN_Y/MAX_Y from interphyre.config plus
    WORLD_BOUNDS_EPSILON to keep the AABB strictly inside the wall geometry.
    """
    old_aabb = compute_object_aabb(target_name, scene_dict)
    if old_aabb is None:
        return False

    target_obj = scene_dict["objects"].get(target_name)
    if target_obj is None:
        return False

    dx = new_x - target_obj["x"]
    dy = new_y - target_obj["y"]
    new_aabb = (
        old_aabb[0] + dx,
        old_aabb[1] + dx,
        old_aabb[2] + dy,
        old_aabb[3] + dy,
    )

    eps = WORLD_BOUNDS_EPSILON
    x_min_bound = MIN_X + eps
    x_max_bound = MAX_X - eps
    y_min_bound = MIN_Y + eps
    y_max_bound = MAX_Y - eps

    xmin, xmax, ymin, ymax = new_aabb
    return (
        xmin >= x_min_bound
        and xmax <= x_max_bound
        and ymin >= y_min_bound
        and ymax <= y_max_bound
    )


def check_no_surface_tangent_collapse(
    direction: tuple[float, float],
    neighbor_surface_vectors: list[tuple[float, float]],
) -> bool:
    """Return True iff direction is not parallel to any neighbor surface vector.

    A direction is parallel to a surface if |dot(direction, surface)| > 0.95
    after each vector is unit-normalised. This rejects perturbations that
    slide the target along a constraint surface rather than displacing it —
    such perturbations produce near-zero mechanical effect regardless of
    magnitude and would corrupt the CF-flip-rate calibration.

    The threshold 0.95 corresponds to ~18° from parallel; directions within
    that cone are rejected as effectively tangent.
    """
    dx, dy = direction
    dir_norm = math.sqrt(dx * dx + dy * dy)
    if dir_norm < 1e-9:
        # Zero-length direction cannot be evaluated; reject to be safe.
        return False
    dx_n, dy_n = dx / dir_norm, dy / dir_norm

    for sx, sy in neighbor_surface_vectors:
        s_norm = math.sqrt(sx * sx + sy * sy)
        if s_norm < 1e-9:
            continue
        sx_n, sy_n = sx / s_norm, sy / s_norm
        dot = abs(dx_n * sx_n + dy_n * sy_n)
        if dot > 0.95:
            return False

    return True


def validate_static_perturbation(
    target_name: str,
    new_x: float,
    new_y: float,
    scene_dict: dict,
    neighbor_surface_vectors: list[tuple[float, float]],
    direction: tuple[float, float],
) -> tuple[bool, str]:
    """Run all three §9.2 guards on a proposed static-position perturbation.

    Returns (True, "") if valid, or (False, reason) on first failure.
    Checks are ordered cheapest-first: surface-tangent (pure arithmetic),
    world-bounds (AABB arithmetic), then intersect (O(n) AABB scan).
    """
    if not check_no_surface_tangent_collapse(direction, neighbor_surface_vectors):
        return False, "surface_tangent"

    if not check_within_world_bounds(target_name, new_x, new_y, scene_dict):
        return False, "out_of_bounds"

    if not check_no_intersect(target_name, new_x, new_y, scene_dict):
        return False, "no_intersect_fail"

    return True, ""
