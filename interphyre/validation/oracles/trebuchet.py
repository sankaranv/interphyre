"""Targeted oracle for trebuchet (the_trebuchet).

A trebuchet: green ball on the RIGHT end of a tilted beam; fulcrum ball is
the pivot.  Action balls dropped near (or slightly left of) the fulcrum
x-coordinate with large radius (1.3–1.5) push the left arm down, launching
the green ball toward the target_ramp on the far right.

The success region is very narrow:
  x within ~0.5 units of fulcrum.x (centered just left of it)
  y in [-0.5, 1.5]
  r in [1.3, 1.5]

Concentrating 80% of attempts in this tight region gives ~1% success
probability per attempt, making 500 attempts sufficient for reliable
validation of the few solvable variants.
"""

from __future__ import annotations


from interphyre.validation.oracles import (
    _run_attempt,
    register_defaults,
    register_oracle,
)

register_defaults("trebuchet", max_variants=50, n_attempts=600)


@register_oracle("trebuchet")
def oracle(level, config, n_attempts, oracle_steps, rng) -> bool:
    from interphyre.environment import InterphyreEnv

    fulcrum = level.objects["fulcrum"]
    beam = level.objects["beam"]
    fx = float(fulcrum.x)
    beam_top = float(beam.top)

    env = InterphyreEnv(level, config=config)
    try:
        for i in range(n_attempts):
            if i % 10 < 8:
                # Tight region: near fulcrum, large radius.
                r = float(rng.uniform(1.3, 1.5))
                ax1 = float(rng.uniform(fx - 0.5, fx + 0.2))
                ay1 = float(rng.uniform(-0.5, 1.5))
                ax2 = float(rng.uniform(fx - 0.5, fx + 0.2))
                ay2 = float(rng.uniform(-0.5, 1.5))
            else:
                # Fallback: left half of beam, moderate radius.
                r = float(rng.uniform(0.7, 1.5))
                ax1 = float(rng.uniform(fx - 1.5, fx + 0.5))
                ay1 = float(rng.uniform(beam_top, 4.0))
                ax2 = float(rng.uniform(fx - 1.5, fx + 0.5))
                ay2 = float(rng.uniform(beam_top, 4.0))

            if _run_attempt(env, [(ax1, ay1, r), (ax2, ay2, r)]):
                return True
    finally:
        env.close()
    return False
