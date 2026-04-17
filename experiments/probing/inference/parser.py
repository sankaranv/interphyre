"""
Action-tag parser for probing inference outputs.

Implements §10.3 parse_action and §11.2 action_anchors. The JSON-in-tag schema
with fixed key order x, y, radius is load-bearing for T2's definition (first comma
in the payload = x/y separator). Do not reorder keys.
"""

from __future__ import annotations

import json
import math
import re

# §10.3: committed action-tag regex. DOTALL so the payload may span newlines.
# Only the first <action>...</action> span is read.
ACTION_TAG_RE = re.compile(r"<action>\s*(\{.*?\})\s*</action>", flags=re.DOTALL)


def parse_action(output_text: str) -> tuple[float, float, float] | None:
    """Return (x, y, radius) from the first well-formed <action>...</action> span.

    Returns None if the span is absent, the JSON payload is malformed, or any
    value is not a finite float. Failure is fail-closed per §10.3: any parse
    error drops the instance. Non-finite values (NaN, inf) would crash the
    physics engine and cannot be matched to a factual outcome.
    """
    match = ACTION_TAG_RE.search(output_text)
    if match is None:
        return None
    try:
        payload = json.loads(match.group(1))
        x = float(payload["x"])
        y = float(payload["y"])
        radius = float(payload["radius"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None
    # Reject non-finite values — they would crash the physics engine.
    if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(radius)):
        return None
    return (x, y, radius)


def action_anchors(output_text: str) -> dict | None:
    """Return byte offsets for T1/T2/T3 anchors per §11.2.

    Locates the first <action>...</action> span and returns:
        {
            "tag_open_byte":    int,  # offset of '<' in '<action>'
            "first_comma_byte": int,  # offset of first ',' inside the JSON payload
        }
    Returns None if the action tag is malformed (instance is dropped per §10.3).

    The first comma in the payload is the x/y separator because the key order
    x, y, radius is fixed by §10.3 — making T2 unambiguous across tokenizers.
    """
    match = ACTION_TAG_RE.search(output_text)
    if match is None:
        return None

    # Byte offset of '<' that opens the <action> tag.
    tag_open_byte = match.start()

    # The JSON payload spans match.start(1)..match.end(1). Find the first ','
    # inside it, which is the x/y separator under the fixed key order.
    payload_text = match.group(1)
    comma_offset = payload_text.find(",")
    if comma_offset == -1:
        # Payload has no comma — malformed JSON (missing y and/or radius).
        return None

    # Absolute byte position of the first comma within output_text.
    first_comma_byte = match.start(1) + comma_offset

    return {
        "tag_open_byte": tag_open_byte,
        "first_comma_byte": first_comma_byte,
    }
