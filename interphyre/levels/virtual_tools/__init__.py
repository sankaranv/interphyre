# Virtual Tools level set — renamed from task01000 through task01011.
# Import all task modules to trigger @register_level decorators.
import importlib

_VT_MODULES = [
    "the_offering",
    "crossing",
    "dead_weight",
    "free_fall",
    "floodgate",
    "low_bridge",
    "the_seal",
    "warden",
    "the_idol",
    "walk_the_plank",
    "the_scaffold",
    "hit_the_deck",
]
for _module in _VT_MODULES:
    importlib.import_module(f"interphyre.levels.virtual_tools.{_module}")
