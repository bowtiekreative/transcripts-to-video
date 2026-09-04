"""Lexicographic candidate ordering (MOTION_MATH.md §9).

A weighted sum lets three fewer marks buy a lie: a template that drops a
semantic obligation can outscore one that keeps it, as long as it is simpler.
A lexicographic order cannot. Truth terms are compared first and the comparison
stops the moment they differ, so no amount of economy reaches past them.

Order, all minimised:

    1.  semantic_loss             hard gate: must be 0
    2.  false_implication_risk    hard gate: must be 0
    3.  relation_mismatch         how exactly the template states THIS relation
    4.  perceptual_accuracy_rank  Cleveland & McGill, only when a quantity is asserted
    4.  simultaneous_chunks       gate: <= 4 (Cowan)
    5.  scan_time_ratio           gate: <= 0.70 (readability)
    6.  mark_count
    7.  visible_words
    8.  motion_events             gate: <= 2
    9.  layout_complexity
    10. stable_hash               deterministic tiebreak
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .utils import stable_hash, word_count

# Which perceptual channel each template uses to carry a magnitude. Templates
# absent from this map do not encode quantity at all, and their accuracy rank
# is only consulted when the scene actually asserts one.
QUANTITY_CHANNEL: dict[str, str] = {
    "big_number": "printed",                 # a printed figure is exact, not perceived
    "bar_chart": "length",
    "matrix": "position_identical_scales",
    "timeline": "position_common_scale",
    "funnel": "area",                        # funnels encode by width; Stevens n≈0.7
    "cycle": "angle",
    "network": "area",
    "hierarchy_tree": "area",
}

# Templates that put an explicit number next to the mark. §8 of the sparseness
# doc: this redundancy earns its ink, because the number survives a glance-away.
DIRECT_LABEL_TEMPLATES = {"big_number", "bar_chart", "timeline", "matrix"}

# How many marks a template puts on screen beyond its own text.
_STRUCTURAL_MARKS = {
    "title_card": 0, "quote_focus": 1, "question_card": 1, "definition_card": 1,
    "warning_card": 1, "cta_card": 2, "big_number": 2,
    "list_stack": 1, "steps": 2, "timeline": 2, "funnel": 2, "condition_cards": 1,
    "before_after": 3, "comparison_split": 3, "transformation_arrow": 3,
    "cause_effect": 3, "problem_solution": 3,
    "network": 2, "cycle": 2, "hierarchy_tree": 2,
    "bar_chart": 2, "audio_wave": 1, "matrix": 3,
}

_LAYOUT_COMPLEXITY = {
    "centered": 0, "vertical_rail": 0, "image_overlay": 1,
    "vertical_stack": 1, "number_rail": 1, "two_column_grid": 2,
    "vertical_path": 2, "horizontal_path": 2, "horizontal_axis": 2,
    "stacked_split": 2, "side_split": 2, "vertical_bridge": 2, "horizontal_bridge": 2,
    "equation_stack": 1, "term_left": 1, "vertical_tree": 3, "horizontal_tree": 3,
    "radial": 3, "offset_hub": 3, "radial_cycle": 3, "qr_split": 2,
    "full_field": 1, "vertical_funnel": 2, "horizontal_funnel": 2,
    "vertical_bars": 2, "horizontal_bars": 2, "matrix_grid": 4,
}

# Which visual slots each template can actually show. A scene obligation that
# lands outside this set is semantic loss, not a styling preference.
TEMPLATE_SLOTS: dict[str, set[str]] = {
    "title_card": {"headline", "entity_label", "time_label"},
    "quote_focus": {"headline", "entity_label"},
    "question_card": {"headline"},
    "definition_card": {"headline", "entity_label", "axis_label"},
    "warning_card": {"headline", "entity_label"},
    "cta_card": {"headline", "entity_label"},
    "big_number": {"hero_mark", "entity_label", "axis_label", "time_label", "headline"},
    "list_stack": {"parts", "headline", "entity_label"},
    "steps": {"parts", "headline", "left", "right"},
    "timeline": {"parts", "time_label", "headline", "left", "right"},
    "funnel": {"parts", "headline"},
    "condition_cards": {"left", "right", "parts", "headline"},
    "before_after": {"left", "right", "headline", "time_label"},
    "comparison_split": {"left", "right", "headline", "axis_label"},
    "transformation_arrow": {"left", "right", "headline"},
    "cause_effect": {"left", "right", "barrier", "blocked", "headline"},
    "problem_solution": {"left", "right", "headline"},
    "network": {"centre", "parts", "headline", "boundary"},
    "cycle": {"parts", "headline"},
    "hierarchy_tree": {"centre", "parts", "boundary", "headline"},
    "bar_chart": {"hero_mark", "parts", "axis_label", "entity_label", "headline"},
    "audio_wave": {"headline"},
    "matrix": {"parts", "axis_label", "headline"},
}


@dataclass(frozen=True)
class OrderKey:
    """The comparison tuple. Every field is minimised."""

    semantic_loss: int
    false_implication_risk: int
    relation_mismatch: int
    perceptual_rank: int
    chunks: int
    scan_ratio: float
    marks: int
    visible_words: int
    motion_events: int
    layout_complexity: int
    tiebreak: str

    def as_tuple(self) -> tuple:
        # scan_ratio is bucketed so that immaterial differences do not outrank
        # the deterministic tiebreak and make selection look unstable.
        return (
            self.semantic_loss,
            self.false_implication_risk,
            self.relation_mismatch,
            self.perceptual_rank,
            self.chunks,
            round(self.scan_ratio, 2),
            self.marks,
            self.visible_words,
            self.motion_events,
            self.layout_complexity,
            self.tiebreak,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "semantic_loss": self.semantic_loss,
            "false_implication_risk": self.false_implication_risk,
            "relation_mismatch": self.relation_mismatch,
            "perceptual_rank": self.perceptual_rank,
            "chunks": self.chunks,
            "scan_ratio": round(self.scan_ratio, 3),
            "marks": self.marks,
            "visible_words": self.visible_words,
            "motion_events": self.motion_events,
            "layout_complexity": self.layout_complexity,
        }


def visible_words_for(template_id: str, payload: dict[str, Any]) -> int:
    """Words the frame actually shows, which is not the same as words spoken."""
    slots = TEMPLATE_SLOTS.get(template_id, set())
    total = word_count(str(payload.get("headline") or ""))
    for key in ("label", "unit", "term", "definition", "supporting", "action", "destination",
                "left", "right", "center", "parent", "number"):
        if payload.get(key):
            total += word_count(str(payload[key]))
    for key in ("items", "nodes", "children"):
        value = payload.get(key)
        if isinstance(value, list):
            total += sum(word_count(str(v)) for v in value)
    events = payload.get("events")
    if isinstance(events, list):
        total += sum(
            word_count(str(e.get("event", ""))) + word_count(str(e.get("time", "")))
            for e in events if isinstance(e, dict)
        )
    series = payload.get("series")
    if isinstance(series, list):
        total += sum(word_count(str(s.get("label", ""))) for s in series if isinstance(s, dict))
    return total


def item_count(payload: dict[str, Any]) -> int:
    for key in ("items", "nodes", "children", "series", "points", "events"):
        value = payload.get(key)
        if isinstance(value, list):
            return len(value)
    return 0


def chunk_count(template_id: str, payload: dict[str, Any]) -> int:
    """Simultaneous visual chunks (Cowan's 4±1), not marks.

    A hero mark plus its label is two chunks and reads instantly. A four-series
    chart with a legend is six and needs a legend-free redesign.
    """
    base = 1
    if payload.get("headline"):
        base += 1
    items = item_count(payload)
    if template_id in {"before_after", "comparison_split", "transformation_arrow",
                       "cause_effect", "problem_solution", "condition_cards"}:
        return base + 2
    if template_id in {"network", "cycle", "hierarchy_tree"}:
        return base + 1 + min(items, 4)
    if items:
        return base + min(items, 6)
    return base


def marks_for(template_id: str, payload: dict[str, Any]) -> int:
    return _STRUCTURAL_MARKS.get(template_id, 2) + item_count(payload)


def scan_seconds(marks: int, visible: int, perception: dict[str, Any]) -> float:
    """t_orient + t_scan + t_read + t_hold (MOTION_MATH.md §1.3)."""
    import math

    fixation = perception.get("fixation", {}) or {}
    reading = perception.get("reading", {}) or {}
    orient = float(fixation.get("orient_seconds", 0.35))
    base = float(fixation.get("scan_base_seconds", 0.30))
    coef = float(fixation.get("scan_log_coefficient", 0.15))
    hold = float(fixation.get("hold_seconds", 0.60))
    rate = float(reading.get("on_screen_words_per_second", 3.0))
    return orient + base + coef * math.log2(max(1, marks) + 1) + visible / max(rate, 0.1) + hold


def perceptual_rank(template_id: str, asserts_quantity: bool, perception: dict[str, Any]) -> int:
    """Cleveland & McGill position. 0 when the scene asserts no quantity.

    Only consulted when a magnitude is actually being communicated: ranking a
    quote card against a title card on graphical-perception accuracy would be
    meaningless.
    """
    if not asserts_quantity:
        return 0
    ranks = (perception.get("magnitude", {}) or {}).get("accuracy_rank", {}) or {}
    channel = QUANTITY_CHANNEL.get(template_id)
    if channel is None:
        # Cannot carry the magnitude at all; that is semantic loss, scored there.
        return 0
    if channel == "printed":
        return 0
    return int(ranks.get(channel, 8))


# Which templates can actually express each image schema. A schema the template
# cannot express is a lost RELATION, which is the most expensive kind of loss:
# the relation is the thing the graphic exists to carry.
SCHEMA_TEMPLATES: dict[str, set[str]] = {
    "container": {"hierarchy_tree", "network"},
    "source_path_goal": {"transformation_arrow", "before_after", "steps", "timeline",
                         "problem_solution", "cause_effect", "condition_cards"},
    "path_open": {"steps", "timeline", "list_stack"},
    "link": {"network", "cycle", "hierarchy_tree"},
    "force": {"cause_effect", "problem_solution", "transformation_arrow"},
    "blockage": {"cause_effect", "problem_solution", "warning_card"},
    "counterforce": {"comparison_split", "before_after"},
    "scale": {"bar_chart", "big_number", "timeline", "matrix"},
    "balance": {"comparison_split", "before_after"},
    "part_whole": {"hierarchy_tree", "list_stack", "funnel"},
    "centre_periphery": {"network", "hierarchy_tree"},
    "cycle": {"cycle", "steps"},
    "merging": {"transformation_arrow", "network"},
    "splitting": {"hierarchy_tree", "network"},
    "iteration": {"list_stack", "steps", "funnel"},
    "full_empty": {"bar_chart", "big_number"},
    "near_far": {"comparison_split", "before_after"},
}


# What a schema needs in the payload before it can be drawn at all. A schema
# detected from a stray preposition, with nothing extracted to fill it, licenses
# a form — it does not demand one.
_SCHEMA_EVIDENCE: dict[str, tuple[str, ...]] = {
    "source_path_goal": ("pair", "items"),
    "force": ("pair",),
    "blockage": ("pair",),
    "counterforce": ("pair",),
    "balance": ("pair",),
    "near_far": ("pair",),
    "link": ("hub",),
    "centre_periphery": ("hub",),
    "container": ("items",),
    "part_whole": ("items",),
    "cycle": ("items",),
    "iteration": ("items",),
    "path_open": ("items",),
    "merging": ("pair", "items"),
    "splitting": ("pair", "items"),
    "scale": ("quantity",),
    "full_empty": ("quantity",),
}


def _payload_evidence(payload: dict[str, Any]) -> set[str]:
    evidence: set[str] = set()
    if payload.get("left") and payload.get("right"):
        evidence.add("pair")
    for key in ("items", "nodes", "children"):
        value = payload.get(key)
        if isinstance(value, list) and len(value) >= 2:
            evidence.add("items")
            break
    if payload.get("center") or payload.get("parent"):
        evidence.add("hub")
    if payload.get("number") or payload.get("series"):
        evidence.add("quantity")
    return evidence


def semantic_loss(template_id: str, semantics: Any, payload: dict[str, Any]) -> int:
    """What this template would throw away. Hard gate: must be 0.

    Three sources, because obligations alone are not enough. Most sentences do
    not evoke a mapped frame, so scoring only frame roles made every template
    tie at zero and handed selection to whichever was sparsest — which is the
    too-sparse failure of MDL, not the minimum-sufficient one.
    """
    showable = TEMPLATE_SLOTS.get(template_id, set())
    lost = 0

    # 1. Frame roles the text actually filled. A headline is always available,
    #    so an obligation that reduces to text is never lost.
    obligations = set(getattr(semantics, "obligations", []) or [])
    lost += len(obligations - showable - {"headline"})

    # 2. The relation itself. If the language encodes a schema AND the payload
    #    carries the structure to draw it, a template that cannot express that
    #    schema is not carrying the claim. Without payload evidence the schema
    #    is only a licence, and dropping it costs nothing.
    evidence = _payload_evidence(payload)
    schema = getattr(semantics, "schema", None)
    if schema and evidence & set(_SCHEMA_EVIDENCE.get(schema, ())):
        expressible = SCHEMA_TEMPLATES.get(schema)
        if expressible and template_id not in expressible:
            lost += 1

    # 3. Structure already extracted into the payload. The payload is evidence
    #    of what the text supports: if a left/right pair was extracted, a
    #    template that shows only a headline discards a relation the source made.
    has_pair = "pair" in evidence
    has_quantity = "quantity" in evidence
    if has_pair and not {"left", "right"} <= showable:
        lost += 1
    if payload.get("number") and "hero_mark" not in showable:
        lost += 1
    if payload.get("term") and payload.get("definition") and "axis_label" not in showable:
        lost += 1
    # The text pass extracts a pair, a figure and a list from the SAME sentence,
    # opportunistically. They are alternate encodings of one claim, not three
    # claims, so a list only counts as lost content when it is the primary
    # structure — otherwise every pair template would be charged for dropping a
    # decomposition of the pair it is already showing.
    if "items" in evidence and not has_pair and not has_quantity and "parts" not in showable:
        lost += 1
    if (payload.get("center") or payload.get("parent")) and "centre" not in showable:
        lost += 1
    if isinstance(payload.get("events"), list) and len(payload["events"]) >= 2 and "time_label" not in showable:
        lost += 1
    return lost


def false_implication_risk(
    template_id: str,
    semantics: Any,
    payload: dict[str, Any],
    context: dict[str, Any],
    perception: dict[str, Any],
) -> int:
    """Ways this template would assert something the source did not. Must be 0."""
    risk = 0
    magnitude = perception.get("magnitude", {}) or {}
    safe_channels = set(magnitude.get("quantity_safe_channels", []) or [])
    channel = QUANTITY_CHANNEL.get(template_id)
    asserts_quantity = bool(getattr(semantics, "requires_numeric", False)) or bool(payload.get("series"))

    # Stevens: area and volume are systematically underestimated, so they may
    # not carry a quantity on their own.
    if asserts_quantity and channel and channel not in safe_channels and channel != "printed":
        risk += 1

    # A chart with no bound data is a picture of a claim, not the claim.
    if template_id in {"bar_chart", "matrix", "funnel"} and not context.get("data_bound"):
        risk += 1

    # The frame's omissions must survive. No initial_value means no before-bar:
    # a two-panel template would fabricate a baseline the speaker never gave.
    unfilled = set(getattr(semantics, "unfilled_core_roles", []) or [])
    if unfilled and template_id in {"before_after", "comparison_split", "transformation_arrow",
                                    "cause_effect", "problem_solution"}:
        if not (payload.get("left") and payload.get("right")):
            risk += 1

    # Negation must be shown and then struck, never rendered as absence.
    negation = getattr(semantics, "negation", None)
    if negation and template_id in {"big_number", "bar_chart", "funnel", "matrix"}:
        risk += 1

    # Weber floor: a difference under ~5% drawn as length asserts a salience
    # that is not perceptually there.
    series = payload.get("series")
    if template_id == "bar_chart" and isinstance(series, list) and len(series) >= 2:
        try:
            values = sorted(float(s.get("value", 0)) for s in series if isinstance(s, dict))
            if values and values[-1] > 0:
                spread = (values[-1] - values[0]) / values[-1]
                if spread < float(magnitude.get("min_drawable_difference", 0.05)):
                    risk += 1
        except (TypeError, ValueError):
            pass
    return risk


def motion_events_for(template_id: str, payload: dict[str, Any]) -> int:
    """Concurrent motion events. A staggered group counts as ONE (common fate)."""
    events = 1
    if template_id in {"before_after", "comparison_split", "transformation_arrow",
                       "cause_effect", "problem_solution"}:
        events += 1          # the bridge draws while the panels enter
    if template_id in {"network", "cycle", "hierarchy_tree"}:
        events += 1          # spokes draw while plates enter
    return events


def density_level(template_id: str, payload: dict[str, Any], chunks: int) -> str:
    if template_id in {"title_card", "quote_focus", "question_card"} and not payload.get("items"):
        return "D1" if payload.get("headline") else "D0"
    if template_id in {"before_after", "comparison_split", "transformation_arrow",
                       "cause_effect", "problem_solution", "definition_card"}:
        return "D2"
    if chunks >= 4 or item_count(payload) >= 4:
        return "D3"
    return "D2"


def relation_mismatch(template: dict[str, Any], primary_relation: str | None) -> int:
    """How far this template is from stating THIS relation exactly.

    Three templates can all express SOURCE-PATH-GOAL without loss and still not
    be equally true: "turns audio into a presentation" is a transformation, and
    calling it a problem and a response asserts a difficulty the sentence never
    claimed. This is a truth term, not an economy one, so it sits above every
    count in the order.
    """
    if not primary_relation:
        return 0
    declared = float((template.get("relations") or {}).get(primary_relation, 0.0))
    return int(round(100.0 - max(0.0, min(100.0, declared))))


def build_key(
    template_id: str,
    layout: str,
    payload: dict[str, Any],
    duration: float,
    semantics: Any,
    context: dict[str, Any],
    perception: dict[str, Any],
    seed: Any,
    scene_id: str,
    template: dict[str, Any] | None = None,
) -> OrderKey:
    asserts_quantity = bool(getattr(semantics, "requires_numeric", False)) or bool(payload.get("series"))
    marks = marks_for(template_id, payload)
    visible = visible_words_for(template_id, payload)
    chunks = chunk_count(template_id, payload)
    required = scan_seconds(marks, visible, perception)
    return OrderKey(
        semantic_loss=semantic_loss(template_id, semantics, payload),
        false_implication_risk=false_implication_risk(template_id, semantics, payload, context, perception),
        relation_mismatch=relation_mismatch(template or {}, context.get("primary_relation")),
        perceptual_rank=perceptual_rank(template_id, asserts_quantity, perception),
        chunks=chunks,
        scan_ratio=required / max(duration, 0.01),
        marks=marks,
        visible_words=visible,
        motion_events=motion_events_for(template_id, payload),
        layout_complexity=_LAYOUT_COMPLEXITY.get(layout, 2),
        tiebreak=stable_hash(seed, scene_id, template_id, layout),
    )
