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
        # Tight rotated AABB for a bar at angle θ (radians, CCW from +x).
        # World-frame half-extents:
        #   half_x = (length/2)|cos θ| + (thickness/2)|sin θ|
        #   half_y = (length/2)|sin θ| + (thickness/2)|cos θ|
        angle = obj.get("angle", 0.0)
        half_l = size["length"] / 2.0
        half_t = size["thickness"] / 2.0
        c, s = abs(math.cos(angle)), abs(math.sin(angle))
        half_x = half_l * c + half_t * s
        half_y = half_l * s + half_t * c
        return (x - half_x, x + half_x, y - half_y, y + half_y)

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

    for name, obj in scene_dict["objects"].items():
        if name == target_name:
            continue
        # Skip dynamic objects: Box2D resolves overlap on the next step, so
        # checking dynamic-vs-static AABB at snapshot time is overly conservative.
        if obj.get("dynamic", False):
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
    """Return True iff the shift does not worsen any existing world-bounds violation.

    Terminal objects (purple_ground, purple_wall) are intentionally placed at
    world boundaries, so an absolute AABB-in-bounds check would reject all shifts.
    Instead, we use a delta-relative check: a perturbation is rejected only if it
    moves an AABB edge FURTHER outside the world than it currently sits. Shifts
    that move a currently-out-of-bounds edge back inside, or that shift along a
    dimension that is already within bounds, are allowed.
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
    ox0, ox1, oy0, oy1 = old_aabb
    nx0, nx1, ny0, ny1 = new_aabb

    # Reject only if the shift makes a boundary violation worse.
    if nx0 < MIN_X + eps and nx0 < ox0 - 1e-9:
        return False
    if nx1 > MAX_X - eps and nx1 > ox1 + 1e-9:
        return False
    if ny0 < MIN_Y + eps and ny0 < oy0 - 1e-9:
        return False
    if ny1 > MAX_Y - eps and ny1 > oy1 + 1e-9:
        return False
    return True


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
