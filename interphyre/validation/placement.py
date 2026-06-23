"""Authoritative action-placement validity check for interphyre.

Both InterphyreEnv (step/action validation) and the oracle registry
(solvability checking) must agree on whether a given ball placement is
legal. Keeping a single implementation here prevents the two from
diverging silently — which previously caused oracles to accept
placements that the environment would reject, or vice versa.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from interphyre.config import MAX_X, MAX_Y, MIN_X, MIN_Y
from interphyre.objects import Basket, Box, Bracket, Wedge
from interphyre.objects.bar import circle_intersects_bar
from interphyre.objects.basket import circle_intersects_basket

if TYPE_CHECKING:
    from interphyre.level import Level


def is_valid_placement(level: "Level", x: float, y: float, radius: float) -> bool:
    """Return True iff placing a ball at (x, y, radius) is a valid action.

    Checks two conditions:
    1. Bounds: the ball must fit fully inside the world boundary.
    2. Collision: the ball must not overlap any non-action level object at its
       initial position. Checked against the static level description, not the
       live Box2D world, to match what InterphyreEnv sees at action time.

    Args:
        level: Level instance providing objects and action_objects.
        x: Ball center x-coordinate.
        y: Ball center y-coordinate.
        radius: Ball radius.

    Returns:
        True if the placement is valid; False otherwise.
    """
    # Bounds check: ball must fit fully inside the world boundary.
    if not (
        MIN_X + radius <= x <= MAX_X - radius and MIN_Y + radius <= y <= MAX_Y - radius
    ):
        return False
    # Collision check against every non-action object in the static level description.
    for name, obj in level.objects.items():
        if name in level.action_objects:
            continue
        if hasattr(obj, "radius"):
            if math.sqrt((x - obj.x) ** 2 + (y - obj.y) ** 2) <= radius + obj.radius:
                return False
        elif hasattr(obj, "length"):
            if circle_intersects_bar(x, y, radius, obj):
                return False
        elif isinstance(obj, Basket):
            if circle_intersects_basket(x, y, radius, obj):
                return False
        elif isinstance(obj, Box):
            # Treat Box as an axis-aligned rectangle (angle=0) for placement checks.
            # Use circle_intersects_bar twice (once per axis) via a temporary Bar-like duck.
            # Simpler: manually check AABB distance.
            nearest_x = max(obj.left, min(x, obj.right))
            nearest_y = max(obj.bottom, min(y, obj.top))
            if math.sqrt((x - nearest_x) ** 2 + (y - nearest_y) ** 2) <= radius:
                return False
        elif isinstance(obj, Bracket):
            # Conservative AABB check using outer dimensions.
            half_ow = obj.outer_width / 2
            nearest_x = max(obj.x - half_ow, min(x, obj.x + half_ow))
            nearest_y = max(obj.y - obj.thickness / 2, min(y, obj.y + obj.outer_height))
            if math.sqrt((x - nearest_x) ** 2 + (y - nearest_y) ** 2) <= radius:
                return False
        elif isinstance(obj, Wedge):
            # Conservative AABB check for the ramp's bounding box.
            ramp_left = min(obj.x1, obj.x2)
            ramp_right = max(obj.x1, obj.x2)
            ramp_top = max(obj.y1, obj.y2)
            ramp_bottom = obj.bottom
            nearest_x = max(ramp_left, min(x, ramp_right))
            nearest_y = max(ramp_bottom, min(y, ramp_top))
            if math.sqrt((x - nearest_x) ** 2 + (y - nearest_y) ** 2) <= radius:
                return False
    return True
