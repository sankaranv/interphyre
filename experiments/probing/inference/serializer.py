"""
Scene-to-text serializer for the probing inference pipeline.

Implements §10.1 scene_to_prompt_body. The output is lossless with respect to
the fields that affect physics: given the produced text and knowledge of the
schema, a reader can reconstruct (type, color, x, y, dynamic, size*) for every
object. Live velocity and angle fields are omitted because all rollouts start
from rest (scene_dict at env.reset()).
"""

from __future__ import annotations

# Per-level natural-language success-condition strings (§10.2 table).
# These are direct paraphrases of each level's success_condition predicate
# to avoid leaking the Python API into the prompt while preserving physical content.
SUCCESS_CONDITIONS_NL: dict[str, str] = {
    "down_to_earth": "the green ball stays in contact with the purple ground bar for at least 3 seconds.",
    "end_of_line": "the green ball stays in contact with the purple wall for at least 3 seconds.",
    "two_body_problem": "the green ball stays in contact with the blue ball for at least 3 seconds.",
    "keyhole": "the green ball stays in contact with the purple pad for at least 3 seconds.",
    "mind_the_gap": "the green ball stays in contact with the purple ground for at least 3 seconds.",
}

_PREAMBLE = (
    "World frame: x ∈ [-5, 5], y ∈ [-5, 5], with +y pointing up and gravity = (0, -9.8) m/s^2.\n"
    "Units: meters for position and size; kilogram·meters/second for impulse (not used by the agent)."
)


def _format_object_line(name: str, obj: dict) -> str:
    """Serialize one object entry as a bullet line.

    Ball:   name: Ball, color, position (x, y), radius R, dynamic/static
    Bar:    name: Bar,  color, position (x, y), length L, thickness T, angle θ rad, dynamic/static
    Basket: name: Basket, color, position (x, y), bottom_width W_b, top_width W_t, height H, dynamic/static

    red_ball is given placeholder position (0.0000, 0.0000) and annotated as the action object,
    regardless of its construction-time coordinates, per §10.1.
    """
    obj_type = obj["type"]
    color = obj["color"]
    is_action_object = name == "red_ball"

    if is_action_object:
        x, y = 0.0, 0.0
    else:
        x, y = obj["x"], obj["y"]

    position_str = f"({x:.4f}, {y:.4f})"
    dynamic_str = "dynamic" if obj["dynamic"] else "static"

    size = obj["size"]
    if obj_type == "Ball":
        size_str = f"radius {size['radius']:.4f}"
    elif obj_type == "Bar":
        # angle is included for losslessness; it is zero at env.reset() but the
        # serializer reads it from scene_dict to capture any construction-time angle.
        angle = obj.get("angle", 0.0)
        size_str = (
            f"length {size['length']:.4f}, thickness {size['thickness']:.4f}, "
            f"angle {angle:.4f} rad"
        )
    elif obj_type == "Basket":
        size_str = (
            f"bottom_width {size['bottom_width']:.4f}, "
            f"top_width {size['top_width']:.4f}, "
            f"height {size['height']:.4f}"
        )
    else:
        size_str = ""

    action_suffix = "  [action object; see below]" if is_action_object else ""

    return (
        f"  - {name}: {obj_type}, {color}, position {position_str}, "
        f"{size_str}, {dynamic_str}{action_suffix}"
    )


def scene_to_prompt_body(scene_dict: dict, level_name: str) -> str:
    """Serialize a scene_dict into the three-block prompt body defined at §10.1.

    Block 1 — coordinate-frame preamble (shared across all levels).
    Block 2 — object inventory, one bullet per object, alphabetically ordered by name.
              red_ball is listed with placeholder position (0, 0) and annotated as the
              action object so the LLM understands it chooses the final placement.
    Block 3 — success-condition line derived from level_name via SUCCESS_CONDITIONS_NL.

    Floats are rounded to 4 decimal places for stable tokenization across Python
    float representations (§10.1 losslessness requirement).

    Args:
        scene_dict: the "objects" sub-dict from InterphyreEnv.describe_scene(), i.e.
                    a mapping from object name to its physics + geometry fields.
        level_name: one of the four levels in PRIMARY_LEVELS or FALLBACK_LEVEL.

    Returns:
        A multi-line string forming the body section of the full prompt.
    """
    objects = scene_dict.get("objects", scene_dict)

    # Sort alphabetically so the output is deterministic regardless of dict insertion order.
    sorted_names = sorted(objects.keys())
    object_lines = [_format_object_line(name, objects[name]) for name in sorted_names]

    inventory_header = "Objects (name, type, color, position, size, dynamic):"
    inventory_block = inventory_header + "\n" + "\n".join(object_lines)

    success_line = f"Success condition: the green ball must remain in contact with the {_target_phrase(level_name)} for at least 3.0 seconds."

    # §10.1: three blocks separated by blank lines
    return "\n\n".join([_PREAMBLE, inventory_block, success_line])


def _target_phrase(level_name: str) -> str:
    """Map level name to the target-object phrase for the success-condition line.

    This parallels SUCCESS_CONDITIONS_NL but formats into the 'must remain in
    contact with ...' sentence structure used in §10.1's concrete example.
    """
    _phrases = {
        "down_to_earth": "purple ground",
        "end_of_line": "purple wall",
        "two_body_problem": "blue ball",
        "keyhole": "purple pad",
        "mind_the_gap": "purple ground",
    }
    return _phrases[level_name]
