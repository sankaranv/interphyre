from interphyre.level import Level
from typing import Callable
import importlib

# Registry for level builders
_level_registry: dict[str, Callable[[int | None], Level]] = {}


# Decorator to build and register a level
def register_level(func: Callable[[int | None], Level]):
    def wrapper(seed: int | None = None) -> Level:
        return func(seed)

    # Get level name by calling the function once with no seed
    level = func(None)
    _level_registry[level.name] = wrapper

    return wrapper


def load_level(name: str, seed: int | None = None) -> Level:
    if name not in _level_registry:
        # Try to dynamically import it
        importlib.import_module(f"interphyre.levels.{name}")
        if name not in _level_registry:
            raise ValueError(f"Level '{name}' could not be registered.")
    return _level_registry[name](seed)


def list_levels() -> list[str]:
    """List all registered level names.

    Returns:
        List of level names sorted alphabetically

    Example:
        >>> from interphyre.levels import list_levels
        >>> levels = list_levels()
        >>> print(levels[:3])
        ['basket_case', 'catapult', 'dive_bomb']
    """
    return sorted(_level_registry.keys())
