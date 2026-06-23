"""Oracle config for task00111 (star_crossed).

The two Cross standingsticks hold the balls in V-shaped cups; the action balls
need to tip the standingsticks or dislodge the target balls.  The geometry
varies enough across variants that increasing the variant search budget is
sufficient — no targeted placement strategy is needed beyond the default.
"""

from interphyre.validation.oracles import register_defaults

register_defaults("task00111", max_variants=20, n_attempts=100)
