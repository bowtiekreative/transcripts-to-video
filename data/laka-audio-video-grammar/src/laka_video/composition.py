"""Composition-level pass (MOTION_MATH.md §10).

Per-scene selection cannot see rhythm. Density, accent budget, carrier
persistence and the ending are properties of the whole piece, so they are
evaluated and enforced here, after every scene has been chosen.

This is the difference between directed work and generated work. A viewer who
reads five scenes sharing one evolving object reads them as ONE argument; five
independently perfect scenes read as five slides.
"""
from __future__ import annotations

from typing import Any

from .ordering import chunk_count, density_level, item_count

_LADDER = ["D0", "D1", "D2", "D3"]

# Templates that fill the frame with the accent colour. Exactly one of these is
# allowed per piece, at the conversion moment.
_ACCENT_BLEED = {"cta_card"}

# Templates whose visual object can persist into the next scene and be mutated
# rather than rebuilt from scratch.
_CARRIER_TEMPLATES = {
    "list_stack", "steps", "timeline", "funnel", "network", "cycle",
    "hierarchy_tree", "bar_chart", "before_after", "comparison_split",
    "transformation_arrow", "cause_effect", "problem_solution", "big_number",
}


def _rank(level: str) -> int:
    return _LADDER.index(level) if level in _LADDER else 2


def _alternates(scene: dict[str, Any], ceiling: str) -> dict[str, Any] | None:
    """Best truth-safe candidate at or below a density ceiling.

    Truth first, still: a candidate that drops an obligation is never an
    acceptable way to fix rhythm.
    """
    selected = scene.get("selection_trace", {}).get("selected", {}) or {}
    base_loss = int((selected.get("order") or {}).get("semantic_loss", 0))
    base_risk = int((selected.get("order") or {}).get("false_implication_risk", 0))
    # Rhythm is a presentation concern and must not buy a worse claim. Ordering
    # the alternates by relation fit stopped a demoted call to action from
    # becoming a warning card because "you don't need" contains a negation.
    ranked = sorted(
        scene.get("selection_trace", {}).get("candidates", []) or [],
        key=lambda c: int((c.get("order") or {}).get("relation_mismatch", 100)),
    )
    for candidate in ranked:
        order = candidate.get("order") or {}
        if int(order.get("semantic_loss", 99)) > base_loss:
            continue
        if int(order.get("false_implication_risk", 99)) > base_risk:
            continue
        payload = scene.get("payload", {}) or {}
        level = density_level(str(candidate.get("template")), payload,
                             int(order.get("chunks", chunk_count(str(candidate.get("template")), payload))))
        if _rank(level) <= _rank(ceiling) and candidate.get("template") != selected.get("template"):
            return candidate
    return None


def apply_composition(
    scenes: list[dict[str, Any]],
    perception: dict[str, Any],
    duration: float,
) -> dict[str, Any]:
    """Enforce what can be enforced, measure the rest. Mutates `scenes`."""
    rhythm = perception.get("rhythm", {}) or {}
    ceiling = str(rhythm.get("after_max_density_ceiling", "D1"))
    accent_budget = int(rhythm.get("accent_bleed_scenes_per_piece", 1))
    carrier_min = float(rhythm.get("carrier_persistence_min_ratio", 0.40))
    target_seconds = float(rhythm.get("target_seconds_per_scene", 7.5))
    tolerance = float(rhythm.get("scene_count_tolerance", 0.20))

    notes: list[str] = []

    # --- density -----------------------------------------------------------
    for scene in scenes:
        payload = scene.get("payload", {}) or {}
        order = (scene.get("selection_trace", {}).get("selected", {}) or {}).get("order") or {}
        chunks = int(order.get("chunks", chunk_count(str(scene.get("template")), payload)))
        scene["density_level"] = density_level(str(scene.get("template")), payload, chunks)

    # --- rhythm: no two consecutive D3 -------------------------------------
    if rhythm.get("no_consecutive_max_density", True):
        for index in range(1, len(scenes)):
            if scenes[index]["density_level"] != "D3" or scenes[index - 1]["density_level"] != "D3":
                continue
            replacement = _alternates(scenes[index], ceiling)
            if replacement is None:
                notes.append(
                    f"{scenes[index]['id']}: two dense scenes in a row and no truth-safe lighter "
                    f"alternate; left as is rather than dropping an obligation"
                )
                continue
            scenes[index]["template"] = replacement["template"]
            scenes[index]["layout"] = replacement["layout"]
            scenes[index]["density_level"] = density_level(
                str(replacement["template"]), scenes[index].get("payload", {}) or {},
                int((replacement.get("order") or {}).get("chunks", 3)),
            )
            scenes[index].setdefault("composition_notes", []).append(
                "density rhythm: demoted after a preceding D3 scene"
            )
            notes.append(f"{scenes[index]['id']}: demoted to {replacement['template']} for density rhythm")

    # --- accent budget: exactly one full-bleed scene ------------------------
    bleed = [s for s in scenes if str(s.get("template")) in _ACCENT_BLEED]
    if len(bleed) > accent_budget:
        # The conversion moment is where the ask actually is: the scene naming a
        # destination or an action. Only when none does is it the last one.
        # A destination is the actual ask — a URL is where the viewer goes. An
        # action verb alone ("Bring the problem") is rhetoric, not conversion.
        with_destination = [s for s in bleed if (s.get("payload") or {}).get("destination")]
        with_action = [s for s in bleed if (s.get("payload") or {}).get("action")]
        keep = (with_destination or with_action or bleed)[-1]
        for scene in bleed:
            if scene is keep:
                continue
            replacement = _alternates(scene, "D2")
            if replacement is not None:
                scene["template"] = replacement["template"]
                scene["layout"] = replacement["layout"]
            scene["accent_bleed"] = False
            scene.setdefault("composition_notes", []).append(
                "accent budget: the piece spends its one saturated frame elsewhere"
            )
            notes.append(f"{scene['id']}: accent bleed withdrawn (budget {accent_budget})")
        keep["accent_bleed"] = True
    elif bleed:
        bleed[-1]["accent_bleed"] = True
    for scene in scenes:
        scene.setdefault("accent_bleed", False)

    # --- carrier persistence -----------------------------------------------
    # A scene carries when it shares a continuity key with its predecessor and
    # both operate on a persistent visual object.
    carriers = 0
    for index in range(1, len(scenes)):
        previous, current = scenes[index - 1], scenes[index]
        shared_key = (
            previous.get("continuity_key")
            and previous.get("continuity_key") == current.get("continuity_key")
        )
        both_carry = (
            str(previous.get("template")) in _CARRIER_TEMPLATES
            and str(current.get("template")) in _CARRIER_TEMPLATES
        )
        same_family = previous.get("template") == current.get("template")
        if shared_key and both_carry:
            current["carrier"] = {"from": previous["id"], "mode": "mutate"}
            carriers += 1
        elif both_carry and same_family:
            current["carrier"] = {"from": previous["id"], "mode": "persist"}
            carriers += 1
    carrier_ratio = carriers / max(1, len(scenes))

    # --- hero rule ----------------------------------------------------------
    for scene in scenes:
        payload = scene.get("payload", {}) or {}
        scene["hero_marks"] = 1 if (payload.get("headline") or payload.get("number")) else 0

    # --- scene count --------------------------------------------------------
    expected = duration / max(target_seconds, 0.1)
    low, high = expected * (1 - tolerance), expected * (1 + tolerance)

    return {
        "scene_count": len(scenes),
        "expected_scene_count": round(expected, 1),
        "scene_count_in_band": low <= len(scenes) <= high,
        "density_histogram": {
            level: sum(1 for s in scenes if s.get("density_level") == level) for level in _LADDER
        },
        "accent_bleed_scenes": sum(1 for s in scenes if s.get("accent_bleed")),
        "accent_budget": accent_budget,
        "carrier_persistence": round(carrier_ratio, 3),
        "carrier_persistence_min": carrier_min,
        "carrier_persistence_met": carrier_ratio >= carrier_min,
        "notes": notes,
    }
