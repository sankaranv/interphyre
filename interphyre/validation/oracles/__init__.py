"""Oracle registry and default oracle for solvability validation.

An oracle is a function that tests whether a level is solvable by attempting
to place action objects such that the success condition is achieved within a
simulation budget. Each level may register a targeted oracle that concentrates
samples in the causally relevant region of the action space. Levels without a
targeted oracle fall back to the default uniform-random oracle.

Oracle function signature:
    oracle(level, config, n_attempts, oracle_steps, rng) -> bool

The oracle returns True as soon as any attempt achieves the success condition;
False if all n_attempts exhaust oracle_steps without success.

Targeted oracle implementations live alongside this file, one module per level
(e.g. oracles/basket_case.py). Each imports @register_oracle from this package
and is imported at the bottom of this file once implemented.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import TYPE_CHECKING

import numpy as np

from interphyre.config import MAX_X, MAX_Y, MIN_X, MIN_Y, SimulationConfig
from interphyre.engine import Box2DEngine
from interphyre.levels import list_levels
from interphyre.objects import Ball

if TYPE_CHECKING:
    from interphyre.level import Level

# Registry mapping level name → targeted oracle function.
_oracle_registry: dict[str, Callable] = {}

# Placement bounds for the default uniform-random oracle.
# The world spans [-5, 5]² but we stay 0.5 units inside the walls.
_PLACEMENT_MIN = -4.5
_PLACEMENT_MAX = 4.5


def register_oracle(level_name: str) -> Callable:
    """Decorator to register a targeted oracle for a level.

    The decorated function must match the oracle signature:
        fn(level, config, n_attempts, oracle_steps, rng) -> bool
    """

    def decorator(fn: Callable) -> Callable:
        _oracle_registry[level_name] = fn
        return fn

    return decorator


def get_oracle(level_name: str) -> Callable:
    """Return the registered oracle for level_name, or the default random oracle."""
    return _oracle_registry.get(level_name, _default_oracle)


def list_oracles() -> dict[str, str]:
    """Return {level_name: 'targeted'|'default'} for all levels in list_levels().

    Useful for auditing which levels have stronger solvability guarantees (via
    targeted oracles sampling the causal region) versus the uniform fallback.
    """
    return {
        level_name: ("targeted" if level_name in _oracle_registry else "default")
        for level_name in list_levels()
    }


def _circle_intersects_bar(cx: float, cy: float, radius: float, bar) -> bool:
    """Check if a circle intersects a (possibly rotated) bar."""
    angle_rad = math.radians(-bar.angle)
    dx, dy = cx - bar.x, cy - bar.y
    local_x = dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
    local_y = dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
    closest_x = max(-bar.length / 2, min(local_x, bar.length / 2))
    closest_y = max(-bar.thickness / 2, min(local_y, bar.thickness / 2))
    return (local_x - closest_x) ** 2 + (local_y - closest_y) ** 2 <= radius**2


def _circle_intersects_basket(cx: float, cy: float, radius: float, basket) -> bool:
    """Check if a circle intersects any wall segment of a basket."""
    hw = basket.total_width / 2
    hh = basket.total_height / 2
    wt = getattr(basket, "wall_thickness", 0.1 * min(basket.total_width, basket.total_height))
    bx, by = basket.x, basket.y
    walls = [
        (bx - hw, by - hh, bx - hw + wt, by + hh),
        (bx + hw - wt, by - hh, bx + hw, by + hh),
        (bx - hw, by - hh, bx + hw, by - hh + wt),
        (bx - hw, by + hh - wt, bx + hw, by + hh),
    ]
    for left, bottom, right, top in walls:
        nearest_x = max(left, min(cx, right))
        nearest_y = max(bottom, min(cy, top))
        if (cx - nearest_x) ** 2 + (cy - nearest_y) ** 2 <= radius**2:
            return True
    return False


def _is_valid_oracle_placement(level: Level, x: float, y: float, radius: float) -> bool:
    """Return True iff placing a ball at (x, y, radius) is a valid action.

    Mirrors InterphyreEnv._is_valid_placement so that oracle attempts are
    restricted to positions that an agent could legally use. This prevents
    oracles from exploiting Box2D position-correction impulses arising from
    overlapping placements — a mechanic that InterphyreEnv rejects.
    """
    # Bounds check: ball must fit fully inside the world boundary.
    if not (MIN_X + radius <= x <= MAX_X - radius and MIN_Y + radius <= y <= MAX_Y - radius):
        return False
    # Collision check: ball must not overlap any non-action level object at its
    # initial position. Checked against the static level description, not the
    # live Box2D world, to match what InterphyreEnv sees at action time.
    for name, obj in level.objects.items():
        if name in level.action_objects:
            continue
        if hasattr(obj, "radius"):
            if math.sqrt((x - obj.x) ** 2 + (y - obj.y) ** 2) <= radius + obj.radius:
                return False
        elif hasattr(obj, "length"):
            if _circle_intersects_bar(x, y, radius, obj):
                return False
        elif hasattr(obj, "total_width"):
            if _circle_intersects_basket(x, y, radius, obj):
                return False
    return True


def _run_attempt(
    level: Level,
    config: SimulationConfig,
    positions: list[tuple[float, float, float]],
    oracle_steps: int,
) -> bool:
    """Run a single oracle attempt and return True if the success condition is met.

    Creates a fresh Box2DEngine, places action objects at positions, then steps
    physics up to oracle_steps times — early-exiting on the first successful step.

    Placement validity is enforced before entering the simulation: any position
    that InterphyreEnv would reject (out of bounds or overlapping a level object)
    causes the attempt to return False immediately. This ensures oracle results
    reflect placements that real agents can legally execute.

    Design note: Box2DEngine._create_world skips action objects, so re-using
    the same Level object across attempts is safe. place_action_objects overwrites
    action object coordinates before they enter the simulation, so stale values
    from prior attempts do not affect the physics.
    """
    for x, y, radius in positions:
        if not _is_valid_oracle_placement(level, x, y, radius):
            return False
    engine = Box2DEngine(level=level, config=config)
    engine.place_action_objects(positions)
    for _ in range(oracle_steps):
        engine.world.Step(
            config.time_step,
            config.velocity_iters,
            config.position_iters,
        )
        engine.time_update(config.time_step)
        if level.success_condition(engine):
            return True
    return False


def _default_oracle(
    level: Level,
    config: SimulationConfig,
    n_attempts: int,
    oracle_steps: int,
    rng: np.random.Generator,
) -> bool:
    """Uniform-random oracle: sample action object placements from [-4.5, 4.5]².

    For each attempt, samples independent (x, y) coordinates for every action
    object. Ball radii are held fixed at the object's configured value; size is
    ignored for bars and baskets (a placeholder 0.0 is passed as required by
    the place_action_objects API).

    Returns True on the first attempt that achieves the success condition.
    """
    # Collect the size parameter for each action object once.
    # For balls the existing radius is preserved; bars/baskets ignore the size field.
    action_sizes = [
        level.objects[name].radius if isinstance(level.objects[name], Ball) else 0.0
        for name in level.action_objects
    ]
    n_objects = len(level.action_objects)

    for _ in range(n_attempts):
        xs = rng.uniform(_PLACEMENT_MIN, _PLACEMENT_MAX, size=n_objects)
        ys = rng.uniform(_PLACEMENT_MIN, _PLACEMENT_MAX, size=n_objects)
        positions = [
            (float(x), float(y), size) for x, y, size in zip(xs, ys, action_sizes)
        ]
        if _run_attempt(level, config, positions, oracle_steps):
            return True
    return False


# Targeted oracle implementations — imported here so they register on package load.
from interphyre.validation.oracles import (  # noqa: E402, F401
    basket_case,
    catapult,
    cliffhanger,
    dive_bomb,
    down_to_earth,
    end_of_line,
    falling_into_place,
    flagpole_sitta,
    just_a_nudge,
    keyhole,
    locust_swarm,
    marble_race,
    mind_the_gap,
    off_the_rails,
    pass_the_parcel,
    pinball_machine,
    seesaw,
    staircase,
    straight_face,
    the_cradle,
    the_funnel,
    tipping_point,
    two_body_problem,
    wedge_issue,
    zebra_crossing,
)
