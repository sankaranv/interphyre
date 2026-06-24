"""task01008 — Towers.

A pyramid of blocks sits on a table.  One specific block (the goal block)
must be knocked to the floor.  The player drops the action ball into the
tower to topple the goal block.
"""

import numpy as np

from interphyre.level import Level
from interphyre.levels import register_level
from interphyre.objects import Ball, Box


@register_level
def build_level(seed=None, variant=0, scene=None) -> Level:
    rng = np.random.default_rng(seed if variant == 0 else (seed, variant))

    base_count = int(rng.integers(2, 6))    # number of blocks in bottom row
    t_height = rng.integers(50, 201)        # table height (VT)
    b_size = rng.integers(15, 41)           # block side length (VT)
    t_pos = rng.integers(10, 401)           # table left x (VT)
    flip = rng.integers(0, 2) == 1

    def ip(v):
        return v / 60 - 5

    def flip_x(x):
        return -x

    # Build pyramid row sizes; max 3 rows total, each ≤ previous row.
    rows = [base_count]
    while rows[-1] > 1 and len(rows) < 3:
        next_count = int(rng.integers(0, rows[-1]))
        if next_count == 0:
            break
        rows.append(next_count)

    t_width = base_count * b_size
    table = Box(
        left=ip(t_pos), right=ip(t_pos + t_width),
        top=ip(t_height), bottom=ip(10),
        dynamic=False, color="black",
    )

    # Floor at y=10 VT.
    floor_h = 10 / 60
    floor = Box(
        left=-5, right=5,
        top=ip(0) + floor_h, bottom=ip(0),
        dynamic=False, color="black",
    )

    # Build all blocks and collect positions.
    block_entries = []   # list of (name, Box)
    total_blocks = sum(rows)
    goal_idx = int(rng.integers(0, total_blocks))
    block_count = 0

    for row_i, n_cols in enumerate(rows):
        # Center this row over the table.
        row_offset = (base_count - n_cols) * b_size // 2
        for col_j in range(n_cols):
            bx_vt = t_pos + row_offset + col_j * b_size + b_size / 2
            by_vt = t_height + row_i * b_size + b_size / 2
            bx = ip(bx_vt)
            by = ip(by_vt)
            if flip:
                bx = flip_x(bx)
            is_goal = block_count == goal_idx
            name = "goal_block" if is_goal else f"block_{row_i}_{col_j}"
            box = Box(
                x=bx, y=by,
                width=b_size / 60, height=b_size / 60,
                dynamic=True, color="gray",
            )
            block_entries.append((name, box))
            block_count += 1

    if flip:
        table = Box(
            left=flip_x(ip(t_pos + t_width)), right=flip_x(ip(t_pos)),
            top=ip(t_height), bottom=ip(10),
            dynamic=False, color="black",
        )

    red_ball = Ball(x=0.0, y=4.0, radius=0.5, color="red", dynamic=True)

    objects = {
        "table": table,
        "floor": floor,
        "red_ball": red_ball,
    }
    for name, box in block_entries:
        objects[name] = box

    return Level(
        name="the_idol",
        objects=objects,
        action_objects=["red_ball"],
        success_condition=lambda engine: engine.is_in_contact_for_duration(
            "goal_block", "floor", engine.config.default_success_time
        ),
    )
