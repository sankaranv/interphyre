"""Oracle config for guillotine (hat_trick).

The basket-and-ramp geometry varies across variants.  Widening the variant
search budget reliably finds a valid geometry without a targeted oracle.
"""

from interphyre.validation.oracles import register_defaults

register_defaults("guillotine", max_variants=50, n_attempts=500)
