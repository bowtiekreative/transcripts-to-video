from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from .ordering import OrderKey, build_key
from .utils import stable_hash, triangular_fit, word_count


@dataclass
class Candidate:
    template: str
    layout: str
    score: float
    positive: dict[str, float]
    penalties: dict[str, float]
    reasons: list[str]
    forced: bool = False

    order_key: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "template": self.template,
            "layout": self.layout,
            "score": round(self.score, 4),
            "order": self.order_key.to_dict() if self.order_key is not None else None,
            "positive": {k: round(v, 4) for k, v in self.positive.items()},
            "penalties": {k: round(v, 4) for k, v in self.penalties.items()},
            "reasons": self.reasons,
            "forced": self.forced,
        }


def _present(payload: dict[str, Any], key: str) -> bool:
    value = payload.get(key)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def _item_count(payload: dict[str, Any], template: dict[str, Any] | None = None) -> int:
    template_id = str((template or {}).get("id", ""))
    if template_id == "condition_cards" and _present(payload, "left") and _present(payload, "right"):
        return 2
    required = set((template or {}).get("required_all", []))
    if {"left", "right"}.issubset(required) and _present(payload, "left") and _present(payload, "right"):
        return 2
    if "number" in required and _present(payload, "number"):
        return 1
    if {"term", "definition"}.issubset(required) and _present(payload, "term") and _present(payload, "definition"):
        return 2
    if {"parent", "children"}.issubset(required) and isinstance(payload.get("children"), list):
        return 1 + len(payload["children"])
    if {"center", "nodes"}.issubset(required) and isinstance(payload.get("nodes"), list):
        return 1 + len(payload["nodes"])
    for key in ("events", "series", "points", "items", "nodes", "children"):
        value = payload.get(key)
        if isinstance(value, list):
            return len(value)
    if _present(payload, "left") and _present(payload, "right"):
        return 2
    if _present(payload, "number"):
        return 1
    return 1 if _present(payload, "headline") else 0


def _visible_words(payload: dict[str, Any], template_id: str) -> int:
    field_map = {
        "title_card": ("headline", "supporting", "label"),
        "quote_focus": ("headline", "label"),
        "big_number": ("number", "label", "unit", "context"),
        "before_after": ("headline", "left", "right", "left_label", "right_label"),
        "comparison_split": ("headline", "left", "right", "criterion"),
        "transformation_arrow": ("headline", "left", "right"),
        "cause_effect": ("headline", "left", "right"),
        "problem_solution": ("headline", "left", "right"),
        "definition_card": ("term", "definition", "label"),
        "hierarchy_tree": ("headline", "parent"),
        "network": ("headline", "center"),
        "cycle": ("headline",),
        "question_card": ("headline",),
        "cta_card": ("headline", "supporting", "action", "destination"),
        "warning_card": ("headline", "supporting"),
        "audio_wave": ("headline", "label"),
        "bar_chart": ("headline", "unit"),
        "funnel": ("headline",),
        "matrix": ("headline",),
        "condition_cards": ("headline", "left", "right"),
    }
    total = sum(word_count(str(payload.get(key, ""))) for key in field_map.get(template_id, ("headline", "supporting")) if isinstance(payload.get(key), (str, int, float)))
    list_keys = {
        "list_stack": ("items", "nodes", "children"),
        "steps": ("items",),
        "hierarchy_tree": ("children",),
        "network": ("nodes",),
        "cycle": ("items", "nodes"),
        "funnel": ("items",),
        "condition_cards": ("items",),
    }.get(template_id, ())
    for key in list_keys:
        if isinstance(payload.get(key), list):
            total += sum(word_count(str(v)) for v in payload[key])
            break
    if template_id == "timeline" and isinstance(payload.get("events"), list):
        total += word_count(str(payload.get("headline", "")))
        total += sum(word_count(str(v.get("time", ""))) + word_count(str(v.get("event", ""))) for v in payload["events"] if isinstance(v, dict))
    if template_id == "bar_chart" and isinstance(payload.get("series"), list):
        total += sum(word_count(str(v.get("label", ""))) + 1 for v in payload["series"] if isinstance(v, dict))
    if template_id == "matrix" and isinstance(payload.get("points"), list):
        total += sum(word_count(str(v.get("label", ""))) for v in payload["points"] if isinstance(v, dict))
    return total


def _data_present(payload: dict[str, Any], context: dict[str, Any]) -> bool:
    return bool(context.get("data_bound")) or any(_present(payload, key) for key in ("series", "points", "values", "x_axis", "y_axis"))


def _hard_constraints(template: dict[str, Any], payload: dict[str, Any], duration: float, aspect: str, context: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    for key in template.get("required_all", []):
        if not _present(payload, key):
            return False, [f"missing required field: {key}"]
    groups = template.get("required_any", [])
    if groups and not any(all(_present(payload, key) for key in group) for group in groups):
        return False, ["none of the required payload groups are complete"]
    count = _item_count(payload, template)
    low, high = template.get("item_range", [0, 999])
    if count < low or count > high:
        return False, [f"item count {count} outside {low}..{high}"]
    if aspect not in template.get("aspects", [aspect]):
        return False, [f"aspect {aspect} unsupported"]
    dlow, dhigh = template.get("duration_range", [0, 9999])
    if duration < max(0.5, dlow * 0.45) or duration > dhigh * 2.2:
        return False, [f"duration {duration:.2f}s far outside {dlow}..{dhigh}s"]
    if template.get("requires_data") and not _data_present(payload, context):
        return False, ["explicit data required"]
    if template.get("id") == "timeline" and context.get("primary_relation") == "timeline":
        events = payload.get("events")
        if not isinstance(events, list) or len(events) < 2 or not any(isinstance(e, dict) and e.get("time") for e in events):
            return False, ["timeline relation requires at least two events and an explicit time marker"]
    return True, reasons


def _choose_layout(layouts: list[str], aspect: str) -> str:
    if not layouts:
        return "centered"
    preferences = {
        "9:16": ("vertical", "stacked", "rail", "centered", "radial", "offset"),
        "4:5": ("vertical", "stacked", "rail", "centered", "side", "radial"),
        "16:9": ("horizontal", "side", "wide", "centered", "radial", "grid"),
        "1:1": ("centered", "radial", "grid", "stacked", "vertical", "side"),
    }.get(aspect, ("centered", "vertical", "horizontal", "side"))
    for preference in preferences:
        for layout in layouts:
            if preference in layout:
                return layout
    return layouts[0]


class TemplateSelector:
    def __init__(
        self,
        template_library: dict[str, Any],
        defaults: dict[str, Any],
        brand: dict[str, Any],
        studio_library: dict[str, Any] | None = None,
        perception: dict[str, Any] | None = None,
    ):
        self.templates = template_library.get("templates", [])
        self.by_id = {t["id"]: t for t in self.templates}
        self.defaults = defaults
        self.brand = brand
        self.studio_library = studio_library or {}
        self.perception = perception or {}

    def select(
        self,
        analysis: dict[str, Any],
        scene: dict[str, Any],
        output: dict[str, Any],
        history: list[dict[str, Any]],
        seed: Any,
        overrides: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> tuple[Candidate, list[Candidate]]:
        overrides = overrides or {}
        context = context or {}
        payload = analysis["payload"]
        duration = max(0.01, float(scene["end"]) - float(scene["start"]))
        aspect = str(output.get("aspect", "9:16"))
        forced_id = str(overrides.get("infographic") or overrides.get("template") or "").strip()
        allowed = set(self.defaults.get("allowed_templates") or []) | set(self.brand.get("allowed_templates") or [])
        denied = set(self.defaults.get("denied_templates") or []) | set(self.brand.get("denied_templates") or [])

        if forced_id:
            template = self.by_id.get(forced_id)
            if template is None:
                raise ValueError(f"Unknown forced infographic template: {forced_id}")
            layout = str(overrides.get("layout") or _choose_layout(template.get("layouts", []), aspect))
            local_context = {**context, "primary_relation": analysis.get("primary_relation")}
            ok, failures = _hard_constraints(template, payload, duration, aspect, local_context)
            candidate = Candidate(
                template=forced_id,
                layout=layout,
                score=1000.0 if ok else 900.0,
                positive={"author_override": 1000.0 if ok else 900.0},
                penalties={} if ok else {"invalid_forced_template": 100.0},
                reasons=["author forced template"] + failures,
                forced=True,
                order_key=build_key(
                    template_id=forced_id, layout=layout, payload=payload, duration=duration,
                    semantics=context.get("semantics"), context=local_context,
                    perception=self.perception, seed=seed, scene_id=str(scene.get("id", "")),
                    template=template,
                ),
            )
            return candidate, [candidate]

        weights = self.defaults.get("selection", {}).get("weights", {})
        penalties_cfg = self.defaults.get("selection", {}).get("penalties", {})
        relation_scores = analysis.get("relation_scores", {})
        max_relation = max(relation_scores.values(), default=1.0)
        candidates: list[Candidate] = []

        for template in self.templates:
            tid = template["id"]
            if allowed and tid not in allowed:
                continue
            if tid in denied:
                continue
            local_context = {**context, "primary_relation": analysis.get("primary_relation")}
            ok, failures = _hard_constraints(template, payload, duration, aspect, local_context)
            if not ok:
                continue
            layout = str(overrides.get("layout") or _choose_layout(template.get("layouts", []), aspect))
            positive: dict[str, float] = {}
            negative: dict[str, float] = {}
            reasons: list[str] = []

            relation_fit = 0.0
            winning_relation = None
            for relation, score in relation_scores.items():
                compatibility = float(template.get("relations", {}).get(relation, 0.0)) / 100.0
                fit = (score / max_relation) * compatibility
                if relation != analysis.get("primary_relation"):
                    fit *= 0.72
                if fit > relation_fit:
                    relation_fit = fit
                    winning_relation = relation
            if relation_fit <= 0 and tid not in {"title_card", "quote_focus", "audio_wave"}:
                continue
            positive["semantic"] = float(weights.get("semantic", 35)) * relation_fit
            if winning_relation:
                reasons.append(f"{winning_relation} compatibility")

            required_fields = list(template.get("required_all", []))
            groups = template.get("required_any", [])
            completeness = 1.0
            if required_fields:
                completeness = sum(1 for key in required_fields if _present(payload, key)) / len(required_fields)
            elif groups:
                completeness = max(sum(1 for key in group if _present(payload, key)) / max(1, len(group)) for group in groups)
            count = _item_count(payload, template)
            ilow, ihigh = template.get("item_range", [0, 999])
            item_center = (ilow + ihigh) / 2.0
            item_span = max(1.0, (ihigh - ilow) / 2.0)
            item_fit = max(0.0, 1.0 - abs(count - item_center) / (item_span + 1.0))
            positive["payload"] = float(weights.get("payload", 15)) * (0.75 * completeness + 0.25 * item_fit)

            dlow, dhigh = template.get("duration_range", [2.0, 16.0])
            positive["timing"] = float(weights.get("timing", 10)) * triangular_fit(duration, float(dlow), float(dhigh))

            visible = _visible_words(payload, tid)
            capacity_by_density = {"sparse": 18, "low": 32, "medium": 58, "high": 110}
            capacity = capacity_by_density.get(template.get("density", "low"), 32)
            if aspect in {"9:16", "4:5"}:
                capacity *= 0.9
            density_fit = min(1.0, capacity / max(1.0, visible))
            positive["density"] = float(weights.get("density", 10)) * density_fit
            if visible > capacity:
                negative["text_capacity"] = min(20.0, (visible - capacity) / max(1.0, capacity) * 14.0)

            positive["aspect"] = float(weights.get("aspect", 8))

            motion_family = template.get("motion_family", "reveal")
            wps = float(scene.get("words_per_second", 0.0))
            energy = float(scene.get("audio_features", {}).get("mean_energy", 0.5))
            audio_fit = 1.0
            if wps > float(self.defaults.get("text", {}).get("dense_speech_wps", 3.2)) and motion_family in {"trace", "accumulate", "transform"}:
                audio_fit -= 0.28
            if energy < 0.25 and motion_family == "pulse":
                audio_fit -= 0.12
            if analysis.get("sensitive") and motion_family in {"pulse", "accumulate"}:
                audio_fit -= 0.22
            positive["audio"] = float(weights.get("audio", 5)) * max(0.0, audio_fit)

            if history:
                prev = history[-1]
                same_key = bool(scene.get("continuity_key") and scene.get("continuity_key") == prev.get("continuity_key"))
                positive["continuity"] = float(weights.get("continuity", 7)) * (0.85 if same_key else 0.45)
                if prev.get("template") == tid:
                    negative["same_previous_template"] = float(penalties_cfg.get("same_previous_template", 8))
            else:
                positive["continuity"] = float(weights.get("continuity", 7)) * 0.5

            window = int(self.defaults.get("selection", {}).get("repeat_window", 3))
            recent = [h.get("template") for h in history[-window:]]
            occurrences = recent.count(tid)
            positive["variation"] = float(weights.get("variation", 5)) * (1.0 if occurrences == 0 else 0.25)
            if occurrences >= 2:
                negative["three_in_window"] = float(penalties_cfg.get("three_in_window", 14))

            positive["brand"] = float(weights.get("brand", 3))
            preferred = overrides.get("preference")
            if preferred and (preferred == tid or (isinstance(preferred, list) and tid in preferred)):
                positive["preference"] = float(weights.get("preference", 2))
            else:
                positive["preference"] = 0.0

            risk = template.get("semantic_risk", "low")
            if risk == "medium":
                negative["semantic_risk"] = float(penalties_cfg.get("medium_risk", 4))
            elif risk == "high":
                negative["semantic_risk"] = float(penalties_cfg.get("high_risk", 10))

            score = sum(positive.values()) - sum(negative.values())
            key = build_key(
                template_id=tid,
                layout=layout,
                payload=payload,
                duration=duration,
                semantics=context.get("semantics"),
                context=local_context,
                perception=self.perception,
                seed=seed,
                scene_id=str(scene.get("id", "")),
                template=template,
                previous_template=str(history[-1].get("template")) if history else None,
            )
            if key.semantic_loss:
                reasons.append(f"drops {key.semantic_loss} semantic obligation(s)")
            if key.false_implication_risk:
                reasons.append(f"{key.false_implication_risk} false-implication risk(s)")
            candidates.append(Candidate(tid, layout, score, positive, negative, reasons, order_key=key))

        if not candidates:
            fallback = self.by_id.get("title_card") or self.templates[0]
            fallback_layout = _choose_layout(fallback.get("layouts", []), aspect)
            # §11 of SEMANTIC_MAPPING.md: congruent > none > incongruent. When
            # nothing fits, kinetic typography is the evidence-based default,
            # not timidity — a wrong graphic is measurably worse than no graphic.
            fallback_candidate = Candidate(
                template=fallback["id"], layout=fallback_layout, score=0.0,
                positive={"fallback": 0.0}, penalties={}, reasons=["no compatible candidate; safe typographic fallback"],
                order_key=build_key(
                    template_id=fallback["id"], layout=fallback_layout, payload=payload,
                    duration=duration, semantics=context.get("semantics"), context=context,
                    perception=self.perception, seed=seed, scene_id=str(scene.get("id", "")),
                    template=fallback,
                ),
            )
            return fallback_candidate, [fallback_candidate]

        # Truth first. A weighted sum lets three fewer marks buy a lie; a
        # lexicographic order stops comparing the moment a truth term differs.
        candidates.sort(key=lambda c: c.order_key.as_tuple())
        selected = candidates[0]
        if str(context.get("selection_mode", "studio")) == "wildcard":
            wildcard = (self.studio_library.get("modes") or {}).get("wildcard") or {}
            limit = max(1, int(wildcard.get("candidate_limit", 3)))
            # Truth-safe means exactly that: no dropped obligation, no false
            # implication, and inside the readability and chunk gates. A score
            # band would let the wildcard reach a candidate the order rejected.
            gate = float(((self.perception.get("fixation") or {}).get("duration_gate_ratio", 0.70)))
            chunk_max = int(((self.perception.get("working_memory") or {}).get("max_simultaneous_marks", 4)))
            pool = [
                candidate for candidate in candidates
                if candidate.order_key is not None
                and candidate.order_key.semantic_loss == 0
                and candidate.order_key.false_implication_risk == 0
                and candidate.order_key.chunks <= chunk_max
                and candidate.order_key.scan_ratio <= gate
            ][:limit]
            if pool:
                choice_hash = stable_hash(seed, scene.get("id"), analysis.get("primary_relation"), "wildcard")
                selected = copy.deepcopy(pool[int(choice_hash[:16], 16) % len(pool)])
                selected.reasons.append(
                    f"deterministic wildcard choice from {len(pool)} top truth-safe candidate"
                    f"{'s' if len(pool) != 1 else ''}"
                )
        return selected, candidates
