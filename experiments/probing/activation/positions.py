"""
Token-position extraction for T1, T2, T3 per §11.2.

Maps the three byte-offset anchors returned by action_anchors() to token indices
in the generated output sequence via the tokenizer's offset mapping. All three
positions are defined by byte offsets into output_text so that the definitions
are tokenizer-invariant; the offset mapping provides the byte-to-token bridge.

T1 — last CoT token before <action>: index immediately preceding the token that
     covers tag_open_byte.
T2 — commitment token: the token covering first_comma_byte (x/y separator in
     the JSON payload, unambiguous because key order is fixed at x, y, radius).
T3 — mean pool over token indices [max(0, t_action - N), t_action) where
     t_action is the index covering tag_open_byte and N = T3_POOL_SIZE (32).
"""

from __future__ import annotations

from experiments.probing.config import T3_POOL_SIZE
from experiments.probing.inference.parser import action_anchors


def byte_offset_to_token_index(
    byte_offset: int,
    offset_mapping: list[tuple[int, int]],
) -> int:
    """Return the token index t such that offset_mapping[t][0] <= byte_offset < offset_mapping[t][1].

    Raises ValueError if no token covers the given byte offset. This can happen
    when byte_offset falls on a special token that has a (0, 0) span or on
    whitespace that was stripped by the tokenizer.
    """
    for token_idx, (start, end) in enumerate(offset_mapping):
        if start <= byte_offset < end:
            return token_idx
    raise ValueError(
        f"No token covers byte offset {byte_offset}. "
        f"Offset mapping spans [{offset_mapping[0][0]}, {offset_mapping[-1][1]}) "
        f"with {len(offset_mapping)} tokens."
    )


def extract_token_positions(
    output_text: str,
    output_ids: list[int],
    tokenizer,
    t3_pool_size: int = T3_POOL_SIZE,
) -> dict | None:
    """Map T1, T2, T3 byte-offset anchors to token indices in output_ids.

    Uses the fast-tokenizer offset mapping (return_offsets_mapping=True) to
    locate the token covering each byte offset. The offset mapping is computed
    over output_text, so all indices are relative to the generated output token
    sequence (not the full prompt+output sequence).

    Returns dict with:
        t1_index:        index of the last CoT token before <action>
        t2_index:        index of the token covering the first comma in the JSON
        t3_indices:      list[int] of token indices for the T3 mean pool window
        t3_pool_count:   actual number of tokens averaged (may be < t3_pool_size)
        t_action_index:  index of the token covering the <action> tag open
    Returns None if action_anchors() returns None (malformed output — drop per §10.3).
    """
    anchors = action_anchors(output_text)
    if anchors is None:
        return None

    # Compute byte-to-token mapping over the output text alone.
    # add_special_tokens=False because output_ids was produced by the model
    # and should not acquire an additional BOS/EOS here.
    encoding = tokenizer(
        output_text,
        return_offsets_mapping=True,
        add_special_tokens=False,
    )
    offset_mapping = encoding["offset_mapping"]

    try:
        t_action_index = byte_offset_to_token_index(
            anchors["tag_open_byte"], offset_mapping
        )
    except ValueError:
        # The <action> tag open byte falls on a token boundary edge case;
        # drop the instance per §10.3's fail-closed policy.
        return None

    try:
        t2_index = byte_offset_to_token_index(
            anchors["first_comma_byte"], offset_mapping
        )
    except ValueError:
        return None

    # T1 is the token immediately before the one covering tag_open_byte.
    # If t_action_index == 0, there is no preceding CoT token — drop instance.
    if t_action_index == 0:
        return None
    t1_index = t_action_index - 1

    # T3: mean pool over [max(0, t_action - N), t_action) exclusive of <action> token.
    t3_start = max(0, t_action_index - t3_pool_size)
    t3_indices = list(range(t3_start, t_action_index))
    t3_pool_count = len(t3_indices)

    # Edge case: no CoT tokens at all before <action> (shouldn't happen under
    # reasoning-mode generation but is handled defensively).
    if t3_pool_count == 0:
        return None

    return {
        "t1_index": t1_index,
        "t2_index": t2_index,
        "t3_indices": t3_indices,
        "t3_pool_count": t3_pool_count,
        "t_action_index": t_action_index,
    }
