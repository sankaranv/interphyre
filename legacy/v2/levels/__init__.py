import importlib
import pkgutil
from phyre2.core.level import Level


def load_level(name: str, seed: int = 42) -> Level:
    name = name.lower()
    module_name = f"phyre2.levels.{name}"
    try:
        mod = importlib.import_module(module_name)
    except ModuleNotFoundError:
        raise ValueError(f"Unknown level: {name}")
    if not hasattr(mod, "build_level"):
        raise ValueError(f"Task module '{name}' has no build_level(seed) function.")
    return mod.build_level(seed=seed)
