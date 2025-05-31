from phyre2.level import Level
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
        importlib.import_module(f"phyre2.levels.{name}")
        if name not in _level_registry:
            raise ValueError(f"Level '{name}' could not be registered.")
    return _level_registry[name](seed)


# TODO - LEVELS NOT IMPLEMENTED
# 00003 - KnockBarOnWall - has issue where green bar is not sitting within the basket
# 00004 - BalanceBeam - needs variable ball size, collision retention, infinite balls
# 00008 - Staircase - change success logic to use phyre2.utils.detect_success_basket
