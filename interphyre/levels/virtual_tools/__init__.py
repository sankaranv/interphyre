# Virtual Tools level set — PHYRE task01000 through task01011.
# Import all task modules to trigger @register_level decorators.
import importlib

_VT_MODULES = [f"task{i:05d}" for i in range(1000, 1012)]
for _module in _VT_MODULES:
    importlib.import_module(f"interphyre.levels.virtual_tools.{_module}")
