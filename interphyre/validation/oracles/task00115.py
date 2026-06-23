"""Oracle config for task00115: expanded search budget."""
from interphyre.validation.oracles import register_defaults
register_defaults("task00115", max_variants=25, n_attempts=200)
