"""
Prompt rendering for the probing inference pipeline.

Implements §10.2: a single shared template with two per-level inserts —
task_description and success_condition_nl. All other text (coordinate frame,
action space, output-format specification, chain-of-thought invitation) is
shared across all four levels so that any H5 transfer result cannot be
attributed to template-wording differences.
"""

from __future__ import annotations

from .serializer import scene_to_prompt_body

# Per-level one-sentence task descriptions (§10.2 table).
# Phrased as imperatives so the model receives a clear goal before the scene body.
TASK_DESCRIPTIONS: dict[str, str] = {
    "down_to_earth": "Place the red ball so that the green ball ends up touching the purple ground bar.",
    "end_of_line": "Place the red ball so that the green ball ends up touching the purple wall at the end of the table.",
    "two_body_problem": "Place the red ball so that the green ball ends up touching the blue ball.",
    "keyhole": "Place the red ball so that the green ball passes through the gap between the two black dividers and ends up touching the purple pad.",
    "mind_the_gap": "Place the red ball so that the green ball falls through the gap between the platforms and ends up touching the purple ground.",
}

# Per-level natural-language success conditions (§10.2 table).
# Direct paraphrases of each level's success_condition predicate; duplicated here
# (rather than importing from serializer) so this module is the single authoritative
# source for all prompt-facing text, keeping §10.2's table in one place.
SUCCESS_CONDITIONS_NL: dict[str, str] = {
    "down_to_earth": "the green ball stays in contact with the purple ground bar for at least 3 seconds.",
    "end_of_line": "the green ball stays in contact with the purple wall for at least 3 seconds.",
    "two_body_problem": "the green ball stays in contact with the blue ball for at least 3 seconds.",
    "keyhole": "the green ball stays in contact with the purple pad for at least 3 seconds.",
    "mind_the_gap": "the green ball stays in contact with the purple ground for at least 3 seconds.",
}

# §10.2: Full prompt template. Python .format() is used — no Jinja2 dependency.
# {task_description}, {scene_body}, and {success_condition_nl} are the only
# per-level substitution points; everything else is fixed.
_PROMPT_TEMPLATE = """\
You are solving a 2D physics puzzle in a Box2D world.

{task_description}

{scene_body}

Action space. You place exactly one red action ball by choosing its center (x, y) in meters
and its radius r in meters, with x ∈ [-5, 5], y ∈ [-5, 5], r ∈ [0.1, 1.5]. The ball is
dynamic (falls under gravity and collides with other objects). You do not control anything
after placement; the simulation runs for up to 500 physics steps at 1/60 s per step.

Success in this world. {success_condition_nl}

Think step by step about how the red ball's placement will propagate through the scene,
taking gravity, collisions, and the shapes and positions of the static and dynamic objects
into account. When you have decided on a placement, emit exactly one line of the form

<action>{{"x": <float>, "y": <float>, "radius": <float>}}</action>

and nothing after it. The JSON payload must parse; x, y, radius must be finite floats in
the ranges above. Do not emit more than one <action> tag. If you are uncertain, still emit
your single best guess in the required format."""


def render_prompt(scene_dict: dict, level_name: str) -> str:
    """Render the full prompt for one scene instance.

    Calls scene_to_prompt_body to produce the scene body, then substitutes it
    together with the per-level task_description and success_condition_nl into
    the shared §10.2 template.

    Args:
        scene_dict: the "objects" sub-dict from InterphyreEnv.describe_scene().
        level_name: one of the four levels in PRIMARY_LEVELS or FALLBACK_LEVEL.

    Returns:
        The complete prompt string ready to be wrapped in a user-turn message.
    """
    scene_body = scene_to_prompt_body(scene_dict, level_name)
    return _PROMPT_TEMPLATE.format(
        task_description=TASK_DESCRIPTIONS[level_name],
        scene_body=scene_body,
        success_condition_nl=SUCCESS_CONDITIONS_NL[level_name],
    )
