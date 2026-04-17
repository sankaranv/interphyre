"""
Instance-level filters for the probing study.

§9.3: The two_body_problem level requires a post-hoc filter to guarantee
the red→green chain structure. The filter reads the contact log — purely
Box2D output — and the scene dict's dynamic flags, neither of which depends
on any probe or learned component, so the filter introduces no new bias
beyond the factual-success conditioning already present throughout (§9.6).
"""

from __future__ import annotations

from interphyre.engine import _WALL_NAMES


def first_dynamic_contact_from_red(
    contact_log: list[dict],
    scene_dict: dict,
) -> str | None:
    """Return red_ball's first dynamic-contact partner, or None.

    Iterates contact_log in simulation-time order (the listener appends
    in step order). Skips non-begin events, world-wall partners, and
    static objects. Returns the first dynamic partner of red_ball.

    contact_log: from env.get_contact_log(). Events have keys
        time, event ∈ {"begin", "end", "invalidate"}, pair, objects.
    scene_dict: from env.describe_scene().
        scene_dict["objects"][name]["dynamic"] carries the static/dynamic flag.
    """
    for event in contact_log:
        if event["event"] != "begin":
            continue
        name_a, name_b = event["objects"]
        if "red_ball" not in (name_a, name_b):
            continue
        partner = name_b if name_a == "red_ball" else name_a
        if partner in _WALL_NAMES:
            continue
        partner_obj = scene_dict["objects"].get(partner)
        if partner_obj is None or not partner_obj["dynamic"]:
            continue
        return partner
    return None


def is_retained_instance(
    level_name: str,
    contact_log: list[dict],
    scene_dict: dict,
) -> bool:
    """Return True iff this instance passes the per-level retention filter.

    For two_body_problem: retain only instances where the first dynamic
    contact from red_ball is green_ball (§9.3 chain requirement).
    For all other levels the filter is trivially True — those levels have
    a fixed chain structure by construction (§2.1).
    """
    if level_name != "two_body_problem":
        return True
    return first_dynamic_contact_from_red(contact_log, scene_dict) == "green_ball"
