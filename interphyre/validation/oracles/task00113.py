"""Oracle config for task00113 (hat_trick).

The basket-and-ramp geometry varies across variants.  Widening the variant
search budget reliably finds a valid geometry without a targeted oracle.
"""

from interphyre.validation.oracles import register_defaults

register_defaults("task00113", max_variants=20, n_attempts=100)
