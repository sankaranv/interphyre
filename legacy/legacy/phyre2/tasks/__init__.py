import os
import importlib

# TODO - LEVELS NOT IMPLEMENTED
# 00003 - KnockBarOnWall - has issue where green bar is not sitting within the basket
# 00004 - BalanceBeam - needs variable ball size, collision retention, infinite balls
# 00008 - Staircase - change success logic to use phyre2.utils.detect_success_basket


def get_task(task_name):
    class_name = "".join([word.capitalize() for word in task_name.split("_")])
    module = importlib.import_module(f"phyre2.tasks.{task_name}")
    task = getattr(module, class_name)()
    return task
