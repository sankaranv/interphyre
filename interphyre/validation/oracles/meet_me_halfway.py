"""Oracle config for meet_me_halfway: expanded search budget."""
from interphyre.validation.oracles import register_defaults
register_defaults("meet_me_halfway", max_variants=25, n_attempts=200)
