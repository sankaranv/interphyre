"""Targeted oracle for marble_race.

Causal chain: left_beam (gray, dynamic) is a horizontal gate resting on two static
black balls. black_ball_2 sits near the LEFT end of the beam (acts as pivot).
black_ball_1 sits near the RIGHT end. Dropping red_ball on the outer right portion
of the beam — between black_ball_1 and the right edge — tips the beam clockwise
(right end down, left end up) around the left pivot. The raised left end opens the
path for green_ball (rolling down left_ramp_2) to pass along the beam and continue
via left_ramp_1 to the basket.

Empirical sweep (seeds 0-29, 50×12 grid) confirmed effective placement:
  x: [black_ball_1.x - 0.10, left_beam.right + 0.30]  (outer right arm past support)
  y: [left_beam.y + 0.15, min(left_beam.y + 2.5, ceiling_bottom - radius - 0.05)]

Physics timing: the full chain (tip → green ball traverse + ramp sequence + basket
contact) requires ≥1000 physics steps (~8 s at 60 Hz). oracle_steps=500 misses ~75%
of solvable seeds. We override to a minimum of 1500 steps so that seeds with small-
radius red balls (which tip more slowly) are correctly classified as solvable.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import register_oracle, register_solver, Box2DEngine
from interphyre.validation.placement import is_valid_placement

# Minimum physics steps required for the causal chain to complete.
# 500-step oracle runs classify most marble_race seeds as "impossible" because
# the multi-ramp path (left_beam → left_ramp_1 → basket) needs ~1000-1500 steps.
_MIN_ORACLE_STEPS = 1500

# Contact pairs that certify causality: the red ball must have physically
# tipped the left_beam gate. A success without this contact means the green
# ball traversed the path without the beam being tipped by the agent.
_CAUSAL_CONTACTS = frozenset({
    frozenset({"red_ball", "left_beam"}),
})


def _run_attempt_verified(engine, level, positions, oracle_steps):
    """Run one attempt and return True only if success was causally linked.

    Uses the same engine-reuse pattern as _run_attempt (reset_attempt clears
    contacts between attempts via ClearContacts()). Requires both (a) the
    success condition to be met and (b) at least one BeginContact event in
    _CAUSAL_CONTACTS. Rejects successes where the red ball made no contact
    with the beam gate.
    """
    for x, y, radius in positions:
        if not is_valid_placement(level, x, y, radius):
            return False
    engine.reset_attempt()
    engine.place_action_objects(positions)
    config = engine.config
    for _ in range(oracle_steps):
        engine.world.Step(config.time_step, config.velocity_iters, config.position_iters)
        engine.time_update(config.time_step)
        if level.success_condition(engine):
            seen_pairs = {
                event["pair"]
                for event in engine.contact_listener.contact_events
                if event["event"] == "begin"
            }
            return bool(_CAUSAL_CONTACTS & seen_pairs)
    return False


@register_solver("marble_race")
def solver(level, config, n_attempts, oracle_steps, rng) -> list[tuple[float, float, float]] | None:
    left_beam = level.objects["left_beam"]
    black_ball_1 = level.objects["black_ball_1"]  # right support
    ceiling = level.objects["ceiling"]
    red_ball = level.objects["red_ball"]

    radius = red_ball.radius

    # Right arm of left_beam: from just left of the right support to just past the
    # right edge. This is the only zone that generates clockwise tipping torque.
    x_min = np.clip(black_ball_1.x - 0.10, -4.5, 4.5)
    x_max = np.clip(left_beam.right + 0.30, -4.5, 4.5)

    # Drop height: above beam surface, but below the ceiling.
    ceiling_bottom = ceiling.y - ceiling.thickness / 2
    y_min = np.clip(left_beam.y + 0.15, -4.5, 4.5)
    y_max = float(np.clip(min(left_beam.y + 2.5, ceiling_bottom - radius - 0.05), -4.5, 4.5))

    # Ensure the chain has enough time to complete even for slow-tipping seeds.
    effective_steps = max(oracle_steps, _MIN_ORACLE_STEPS)

    # Degenerate geometry: beam too close to ceiling — no valid drop zone exists.
    if y_max <= y_min:
        return None

    engine = Box2DEngine(level=level, config=config)
    for _ in range(n_attempts):
        x = rng.uniform(x_min, x_max)
        y = rng.uniform(y_min, y_max)
        if _run_attempt_verified(engine, level, [(x, y, radius)], effective_steps):
            return [(x, y, radius)]
    return None


@register_oracle("marble_race")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None
