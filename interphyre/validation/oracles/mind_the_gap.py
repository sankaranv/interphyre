"""Targeted oracle for mind_the_gap.

Causal chain: green_ball at (0, 3.5) falls freely. A blocking_ball sits near
one edge of the hole between left_platform and right_platform. The oracle places
red_ball on the FAR SIDE of green_ball (opposite to the hole) at a near-horizontal
contact angle so the impact deflects green_ball TOWARD the hole. As green_ball
falls, it contacts blocking_ball, displacing it and clearing the hole, then falls
through to purple_ground.

B4 fix: the old oracle used push_offset = sum_of_radii + 0.1–1.5, placing
red_ball OUTSIDE contact range. Both balls free-fall in parallel and never
collide — so green_ball never receives a lateral impulse. The fix uses
x_offset < sum_of_radii (near-horizontal placement just above green_ball),
guaranteeing contact and maximising the lateral component of the impulse.

Fix (this version): Full-board sweeps of impossible-only seeds revealed a
SECOND causal path: placing red_ball at y ∈ [−1.3, 2.5] (well below green_ball's
starting y ≈ 3.5) solves ~42% of the seeds previously classified as impossible.
These low-y placements intercept green_ball after it has fallen further, using a
different deflection geometry. All valid low-y hits have x ∈ [−1.3, 1.3].

Note: an earlier docstring claimed "only seeds with platform_y ≤ ~-3.05 are
solvable". A follow-up sweep of 30 previously-impossible seeds found 29/30
solvable with platform_y > -3.05 once Zone B was active. That claim was an
artifact of the Zone-A-only oracle and has been removed.

Zone C audit note: a Zone C targeting the blocking_ball directly was tested
but reduced performance from 14/20 to 13/20 at n=500 by taking budget from
Zone A/B. The seeds not recovered by A+B (seeds 675, 1238, 1575 confirmed)
are genuinely impossible via 19×19 grid search across 10 variants. The fix
is to increase n_attempts to 200, which reduces the miss probability for
low-hit-rate seeds without adding competing zones.

Fix: Two sampling zones (cycled 1:1):

Zone A (50% of attempts): original tangent push near green_ball.y.
  Preserves 100% per-trial success for the ~246/1000 seeds that this solved.

Zone B (50% of attempts): x near hole center (±1.5), y in [−3.0, green_ball.y − 0.5].
  Covers the second causal path confirmed by sweep. x bounds tightened to
  hole_cx ± 1.5 (sweep window was x ∈ [−1.0, 1.5]); y-min raised to -3.0
  (sweep found all solutions at y ≥ -2.821; -3.0 gives margin without wasting
  samples on the dead zone below -3.0).

Also adds register_solver so the bundle stores the winning placement.
"""

from __future__ import annotations

import numpy as np

from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
    register_solver,
    Box2DEngine,
)


@register_solver("mind_the_gap")
def solver(
    level, config, n_attempts, oracle_steps, rng
) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    left_platform = level.objects["left_platform"]
    right_platform = level.objects["right_platform"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius
    sum_r = green_ball.radius + radius

    # Hole center: used by both zones.
    hole_cx = (left_platform.right + right_platform.left) / 2
    push_direction = 1.0 if hole_cx > green_ball.x else -1.0

    # Zone B bounds: x near hole (±1.5), y below green_ball.
    x_b_min = float(np.clip(hole_cx - 1.5, -4.5, 4.5))
    x_b_max = float(np.clip(hole_cx + 1.5, -4.5, 4.5))
    y_b_max = float(np.clip(green_ball.y - 0.5, -4.5, 4.5))

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        if i % 2 == 0:
            # Zone A (50%): tangent push near green_ball — original mechanism.
            x_offset = rng.uniform(sum_r * 0.6, sum_r * 0.99)
            x = float(np.clip(green_ball.x - push_direction * x_offset, -4.5, 4.5))
            y_clearance = np.sqrt(max(0.0, sum_r**2 - x_offset**2))
            y = rng.uniform(
                green_ball.y + y_clearance + 0.02, green_ball.y + y_clearance + 0.5
            )
        else:
            # Zone B (50%): x near hole center, y below green_ball.
            # Sweep confirmed valid placements at y ∈ [−1.3, 2.5] for ~42% of
            # previously-impossible seeds; all have x ∈ [−1.3, 1.3].
            x = rng.uniform(x_b_min, x_b_max)
            y = rng.uniform(-3.0, y_b_max)

        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("mind_the_gap")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None


# Geometric-decay analysis (2026-04-14): p=0.398 per variant, model(k=20)=0.4 impossible.
# k=20 reduces expected impossible from 62 (k=10) to <1 per 10001 seeds.
# n_attempts raised 200→300 after audit: seed 6719 had 2 solvable variants out of 30
# with narrow solution region (~0.1 sq units in Zone B); 300 attempts raises per-variant
# P(find) from ~43% to ~59%, reducing P(miss both solvable variants) from 0.25 to 0.17.
# Combined with hole_width 1.05→1.15 (level edit), expect 0 impossible seeds.
register_defaults("mind_the_gap", max_variants=20, n_attempts=300)
