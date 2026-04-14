"""Targeted oracle for staircase.

Causal chain: green_ball starts at the top (MAX_Y). Stairs step it down to the
right. The purple_basket is at the bottom, guarded by left/right guard bars.
Drop red_ball anywhere along the staircase path to route green_ball into the
basket.

Prior oracle history:
- Original: x in [cx ± 2.0], y in [green_ball.y - 0.5, green_ball.y + 1.0]
  → collapsed to y ∈ [4.20, 4.50] (0.3-unit dead zone). Fixed: y covers full
  staircase descent [stair_bottom - 0.5, green_ball.y + 0.5].

x sampling: solution x std=2.22 over 10001 seeds — essentially uniform. A
two-Gaussian mixture (50% near green_ball, 30% near basket) gave only 4.3%
avg_var improvement, confirming that targeted x-sampling is ineffective.
Uniform x over the full board is optimal.

y sampling: solution y is multi-modal at discrete stair heights (measured:
mean=2.65, std=1.15 across valid bundle). Each stair provides a distinct
interception point for the green_ball as it descends. Zone A concentrates
80% of y-samples at stair heights using a Gaussian mixture (σ=0.4 per stair)
to exploit this structure. Zone B retains uniform [y_min, y_max] as a fallback
for placements between stairs or at non-stair y-positions.
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


@register_solver("staircase")
def solver(
    level, config, n_attempts, oracle_steps, rng
) -> list[tuple[float, float, float]] | None:
    green_ball = level.objects["green_ball"]
    red_ball = level.objects["red_ball"]
    radius = red_ball.radius

    # Stair y-positions: sorted bottom-to-top. Used for Zone A y-mixture.
    # Solution y is multi-modal at discrete stair heights (mean=2.65, std=1.15
    # across valid bundle) — each stair is a distinct interception point.
    stair_ys = sorted(
        level.objects[k].y for k in level.objects if k.startswith("stair_")
    )
    y_min = float(np.clip(min(stair_ys) - 0.5, -4.5, 4.5)) if stair_ys else -4.5
    y_max = float(np.clip(green_ball.y + 0.5, -4.5, 4.5))

    engine = Box2DEngine(level=level, config=config)
    for i in range(n_attempts):
        # x: full-board uniform in all zones (solution x std=2.22, essentially uniform).
        x = rng.uniform(-4.5, 4.5)

        if i % 5 < 4:
            # Zone A (80%): y sampled from Gaussian mixture over stair heights.
            # Each stair provides a distinct interception point; concentrating samples
            # near stair y-positions targets the multi-modal solution y distribution.
            # σ=0.4 covers placement tolerance around each stair top surface.
            target_stair_y = stair_ys[rng.integers(len(stair_ys))]
            y = float(np.clip(rng.normal(target_stair_y, 0.4), y_min, y_max))
        else:
            # Zone B (20%): uniform fallback covering the full y range.
            # Captures placements between stairs or at non-stair y-positions.
            y = rng.uniform(y_min, y_max)

        if _run_attempt(engine, level, [(x, y, radius)], oracle_steps):
            return [(x, y, radius)]
    return None


@register_oracle("staircase")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    return solver(level, config, n_attempts, oracle_steps, rng) is not None


# Staircase oracle: uniform x (full board) + Zone A y-mixture over stair heights.
# Zone A (80%): y ~ N(stair_y, σ=0.4) for uniform-random stair; Zone B (20%): uniform.
# Trivial rate=11.3%; oracle p_nontrivial~37%; max_variants=25 keeps miss rate low.
register_defaults("staircase", max_variants=25, n_attempts=500)
