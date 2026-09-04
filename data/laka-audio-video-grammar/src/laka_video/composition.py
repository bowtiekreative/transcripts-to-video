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

import re

from .ordering import chunk_count, density_level, item_count

_LADDER = ["D0", "D1", "D2", "D3"]

# Templates that fill the frame with the accent colour. Exactly one of these is
# allowed per piece, at the conversion moment.
_ACCENT_BLEED = {"cta_card"}

# Geometry families. Two scenes in the same family are drawing the SAME visual
# object with different content in it — a rail being refilled, a pair of panels
# being replaced, a hub gaining new spokes. That is what "appear, mutate,
# transform, exit" means: the object persists even when the subject changes,
# and a run of them reads as one argument rather than a stack of slides.
from .ordering import GEOMETRY_FAMILY as _GEOMETRY_FAMILY

_CARRIER_TEMPLATES = set(_GEOMETRY_FAMILY)


# Words that are never the thing a scene is about.
_NOT_SALIENT = {
    "the", "a", "an", "and", "or", "but", "so", "of", "to", "in", "on", "at",
    "for", "from", "with", "by", "as", "that", "this", "these", "those", "it",
    "its", "is", "are", "was", "were", "be", "been", "we", "you", "they", "he",
    "she", "our", "your", "their", "my", "his", "her", "what", "how", "when",
    "why", "who", "which", "there", "here", "then", "than", "into", "out",
    "about", "over", "under", "more", "most", "some", "any", "all", "one",
    "thing", "things", "way", "ways", "kind", "sort", "lot", "time", "times",
    "people", "something", "everything", "anything", "nothing",
}

_PROPER = re.compile(r"\b([A-Z][a-zA-Z]{2,}(?:\s+[A-Z][a-zA-Z]{2,})*)\b")


def _salient_entities(scene: dict[str, Any]) -> set[str]:
    """What this scene is ABOUT, as opposed to what it happens to say.

    The old continuity key was the first content word of the headline, which is
    close to a random token: adjacent scenes almost never matched it and carrier
    persistence sat at zero for the whole film.
    """
    payload = scene.get("payload", {}) or {}
    semantics = scene.get("semantics", {}) or {}
    found: set[str] = set()

    # Proper nouns are the strongest identity signal a transcript offers. A
    # capital at position 0 is NOT discarded: "HouseSmart now ships weekly"
    # opens with the very entity the scene is about. Sentence-openers are
    # removed by the _NOT_SALIENT filter at the end instead, which does not
    # depend on where the word happens to sit.
    for field in ("headline", "left", "right", "center", "parent", "term", "supporting"):
        value = payload.get(field)
        if isinstance(value, str):
            for match in _PROPER.finditer(value):
                found.add(match.group(1).strip().lower())
    for entry in (payload.get("items") or []) + (payload.get("nodes") or []):
        if isinstance(entry, str):
            for match in _PROPER.finditer(entry):
                found.add(match.group(1).strip().lower())

    # The rated head noun, and the head word of each frame role filler.
    head = semantics.get("head_noun")
    if head and head not in _NOT_SALIENT:
        found.add(str(head).lower())
    for filler in (semantics.get("roles") or {}).values():
        tokens = [re.sub(r"[^\w-]", "", t.lower()) for t in str(filler).split()]
        tokens = [t for t in tokens if t and t not in _NOT_SALIENT and len(t) > 3]
        if tokens:
            found.add(tokens[-1])
    # Most sentences carry no proper noun at all. The head words of the
    # headline are then the only identity available, and without them a scene
    # about "the migration" shares nothing with the next scene about it.
    headline = payload.get("headline")
    if isinstance(headline, str):
        tokens = [re.sub(r"[^\w-]", "", t.lower()) for t in headline.split()]
        content = [t for t in tokens if t and len(t) > 4 and t not in _NOT_SALIENT]
        # Subject and object both carry identity: taking only the tail missed
        # "migration" in "The migration finished last quarter", so the next
        # scene about the migration shared nothing with it.
        found.update(content[:1] + content[-2:])

    return {value for value in found if value and value not in _NOT_SALIENT}


def _shared_entities(previous: dict[str, Any], current: dict[str, Any]) -> list[str]:
    before, after = _salient_entities(previous), _salient_entities(current)
    direct = before & after
    if direct:
        return sorted(direct)
    # Given information is by definition already established, so if the current
    # scene's given half overlaps the previous scene at all, the object is
    # already on screen and does not need to be introduced again (SEMANTIC
    # MAPPING §6, the given-new contract).
    given = str((current.get("semantics") or {}).get("given") or "")
    if given:
        tokens = {re.sub(r"[^\w-]", "", t.lower()) for t in given.split()}
        tokens = {t for t in tokens if t and t not in _NOT_SALIENT and len(t) > 3}
        overlap = tokens & before
        if overlap:
            return sorted(overlap)
    return []


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
        # A segment carrying no proposition earns a caption and nothing else.
        # This is the coherence principle with a switch on it: removing
        # decorative material improves comprehension, and discourse filler is
        # exactly that.
        if (scene.get("event") or {}).get("signal") is False:
            scene["density_level"] = "D0"
            scene.setdefault("composition_notes", []).append(
                "EventMath classified this segment as noise; it carries a caption only"
            )

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
        shared = _shared_entities(previous, current)
        same_family = previous.get("template") == current.get("template")
        if shared:
            # The object is already on screen: the scene mutates it rather than
            # rebuilding it, which is what makes a run of scenes read as one
            # argument instead of a stack of slides.
            current["carrier"] = {
                "from": previous["id"],
                "mode": "mutate" if not same_family else "persist",
                "shared": shared[:4],
            }
            carriers += 1
        elif _GEOMETRY_FAMILY.get(str(previous.get("template"))) == _GEOMETRY_FAMILY.get(str(current.get("template"))) \
                and str(current.get("template")) in _GEOMETRY_FAMILY:
            # Same object, new content. The geometry holds across the cut, so
            # the frame is not restated from nothing.
            current["carrier"] = {"from": previous["id"], "mode": "frame", "shared": []}
            carriers += 1
    carrier_ratio = carriers / max(1, len(scenes))

    # How many cuts COULD have continued the object without dropping an
    # obligation. If this is also low, the piece genuinely changes subject and
    # shape every scene, and persistence is a property of the material rather
    # than something the compiler declined to exploit. Saying which is the
    # difference between a useful report and a nag.
    opportunities = 0
    for index in range(1, len(scenes)):
        family = _GEOMETRY_FAMILY.get(str(scenes[index - 1].get("template")))
        if not family:
            continue
        selected = (scenes[index].get("selection_trace", {}).get("selected", {}) or {}).get("order") or {}
        base_loss = int(selected.get("semantic_loss", 0))
        base_risk = int(selected.get("false_implication_risk", 0))
        base_mismatch = int(selected.get("relation_mismatch", 0))
        for candidate in scenes[index].get("selection_trace", {}).get("candidates", []) or []:
            order = candidate.get("order") or {}
            if _GEOMETRY_FAMILY.get(str(candidate.get("template"))) != family:
                continue
            if (int(order.get("semantic_loss", 99)) <= base_loss
                    and int(order.get("false_implication_risk", 99)) <= base_risk
                    and int(order.get("relation_mismatch", 999)) <= base_mismatch):
                opportunities += 1
                break
    opportunity_ratio = opportunities / max(1, len(scenes))

    # --- hero rule ----------------------------------------------------------
    for scene in scenes:
        payload = scene.get("payload", {}) or {}
        scene["hero_marks"] = 1 if (payload.get("headline") or payload.get("number")) else 0

    # --- scene count --------------------------------------------------------
    expected = duration / max(target_seconds, 0.1)
    low, high = expected * (1 - tolerance), expected * (1 + tolerance)

    # Reported, not warned about: a compiler forbidden from paraphrasing cannot
    # move this number without breaking its own determinism guarantee.
    shares = []
    for scene in scenes:
        budget = scene.get("reading_budget") or {}
        if budget.get("spoken_words"):
            shares.append(budget.get("speech_share", 0.0))
    return {
        "speech_share_mean": round(sum(shares) / len(shares), 3) if shares else 0.0,
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
        "carrier_opportunities": round(opportunity_ratio, 3),
        "notes": notes,
    }
