from __future__ import annotations

from collections import Counter
from typing import Any

from .utils import word_count


def _issue(severity: str, code: str, message: str, scene_id: str | None = None) -> dict[str, Any]:
    item = {"severity": severity, "code": code, "message": message}
    if scene_id:
        item["scene_id"] = scene_id
    return item


def lint_storyboard(storyboard: dict[str, Any], defaults: dict[str, Any], template_library: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    scenes = storyboard.get("scenes", [])
    composition = storyboard.get("composition", {})
    duration = float(composition.get("duration", 0.0))
    templates = {t["id"]: t for t in template_library.get("templates", [])}
    max_words = int(defaults.get("text", {}).get("max_words_on_screen", 18))
    min_scene = float(defaults.get("timing", {}).get("min_scene_seconds", 3.5))
    max_scene = float(defaults.get("timing", {}).get("max_scene_seconds", 12.0))
    min_resolve = float(defaults.get("timing", {}).get("min_resolve_seconds", 0.8))

    if duration <= 0:
        issues.append(_issue("FATAL", "composition.duration", "Composition duration must be positive."))
    if not scenes:
        issues.append(_issue("FATAL", "composition.scenes", "No scenes were compiled."))

    previous_end = 0.0
    recent_templates: list[str] = []
    for index, scene in enumerate(scenes):
        sid = str(scene.get("id", f"scene-{index + 1}"))
        start = float(scene.get("start", 0.0))
        end = float(scene.get("end", 0.0))
        scene_duration = end - start
        if end <= start:
            issues.append(_issue("ERROR", "timing.nonpositive", f"Scene duration is {scene_duration:.3f}s.", sid))
        if start < -1e-4 or end > duration + 1e-3:
            issues.append(_issue("ERROR", "timing.out_of_bounds", f"Scene {start:.3f}–{end:.3f}s exceeds composition 0–{duration:.3f}s.", sid))
        if index > 0:
            if start > previous_end + 0.08:
                issues.append(_issue("WARNING", "timing.gap", f"Uncovered visual gap of {start - previous_end:.3f}s.", sid))
            elif start < previous_end - 0.08:
                issues.append(_issue("WARNING", "timing.overlap", f"Scene overlaps previous scene by {previous_end - start:.3f}s.", sid))
        previous_end = max(previous_end, end)

        if scene_duration < min_scene and not scene.get("allow_short_scene"):
            issues.append(_issue("INFO", "timing.short_scene", f"Scene is shorter than the {min_scene:.1f}s default.", sid))
        if scene_duration > max_scene * 1.55:
            issues.append(_issue("WARNING", "timing.long_scene", f"Scene is {scene_duration:.1f}s; consider splitting or pagination.", sid))
        if scene_duration < min_resolve:
            issues.append(_issue("ERROR", "timing.no_resolve", "Scene is too short to establish a readable final state.", sid))

        template_id = scene.get("template")
        template = templates.get(template_id)
        if template is None:
            issues.append(_issue("ERROR", "template.unknown", f"Unknown template: {template_id}", sid))
        else:
            relation = scene.get("primary_relation")
            relation_weight = float(template.get("relations", {}).get(relation, 0.0))
            if relation_weight <= 0 and not scene.get("selection_trace", {}).get("selected", {}).get("forced"):
                issues.append(_issue("WARNING", "semantic.weak_template", f"Template {template_id} does not declare compatibility with {relation}.", sid))
            for key in template.get("required_all", []):
                if not scene.get("payload", {}).get(key):
                    issues.append(_issue("ERROR", "payload.missing", f"Template {template_id} requires payload.{key}.", sid))
            groups = template.get("required_any", [])
            if groups and not any(all(scene.get("payload", {}).get(key) for key in group) for group in groups):
                issues.append(_issue("ERROR", "payload.incomplete_group", f"Template {template_id} has no complete required payload group.", sid))
            if template.get("requires_data") and not scene.get("data_bound"):
                issues.append(_issue("ERROR", "data.required", f"Template {template_id} requires explicit source data.", sid))

        payload = scene.get("payload", {})
        if scene.get("layout") == "image_overlay" and not (scene.get("asset") or payload.get("asset")):
            issues.append(
                _issue(
                    "ERROR",
                    "asset.required",
                    "Image + headline requires a filled image slot before rendering.",
                    sid,
                )
            )
        headline_words = word_count(str(payload.get("headline", "")))
        template_fields = {
            "title_card": ["supporting", "label"], "quote_focus": ["label"],
            "big_number": ["label", "unit"], "before_after": ["left", "right"],
            "comparison_split": ["left", "right"], "transformation_arrow": ["left", "right"],
            "cause_effect": ["left", "right"], "problem_solution": ["left", "right"],
            "definition_card": ["term", "definition"], "hierarchy_tree": ["parent"],
            "network": ["center"], "cta_card": ["supporting", "action", "destination"],
            "warning_card": ["supporting"],
        }.get(template_id, [])
        visible_estimate = headline_words + sum(word_count(str(payload.get(k, ""))) for k in template_fields)
        list_key = {"list_stack":"items", "steps":"items", "hierarchy_tree":"children", "network":"nodes", "cycle":"items", "funnel":"items", "condition_cards":"items"}.get(template_id)
        if list_key and isinstance(payload.get(list_key), list):
            visible_estimate += sum(word_count(str(x)) for x in payload[list_key])
        if template_id == "timeline" and isinstance(payload.get("events"), list):
            visible_estimate += sum(word_count(str(x.get("time", ""))) + word_count(str(x.get("event", ""))) for x in payload["events"] if isinstance(x, dict))
        if visible_estimate > max_words * 2.6:
            issues.append(_issue("WARNING", "layout.text_density", f"Estimated visible load is {visible_estimate} words.", sid))

        motion = scene.get("motion", {})
        if scene.get("words_per_second", 0) > defaults.get("text", {}).get("dense_speech_wps", 3.2):
            if motion.get("magnitude") in {"large", "hero"} or motion.get("frequency") in {"continuous", "per_word"}:
                issues.append(_issue("WARNING", "motion.dense_speech", "Motion may compete with dense narration.", sid))
        if scene.get("sensitive") and motion.get("detectability") == "dominant":
            issues.append(_issue("WARNING", "motion.sensitive_content", "Dominant motion is discouraged for sensitive content.", sid))

        recent_templates.append(str(template_id))
        if len(recent_templates) >= 3 and len(set(recent_templates[-3:])) == 1:
            issues.append(_issue("INFO", "variation.template_repeat", f"Template {template_id} appears three times consecutively.", sid))

    captions = storyboard.get("captions", [])
    last_caption_end = -1.0
    for caption in captions:
        t0 = float(caption.get("t0", 0))
        t1 = float(caption.get("t1", 0))
        if t1 <= t0:
            issues.append(_issue("ERROR", "caption.nonpositive", "Caption has nonpositive duration."))
        if t0 < last_caption_end - 0.08:
            issues.append(_issue("WARNING", "caption.overlap", "Caption chunks overlap."))
        if t1 > duration + 0.05:
            issues.append(_issue("ERROR", "caption.out_of_bounds", "Caption exceeds composition duration."))
        last_caption_end = max(last_caption_end, t1)

    severities = Counter(issue["severity"] for issue in issues)
    deductions = (
        severities.get("FATAL", 0) * 30
        + severities.get("ERROR", 0) * 8
        + severities.get("WARNING", 0) * 2.5
        + severities.get("INFO", 0) * 0.25
    )
    score = max(0.0, 100.0 - deductions)
    status = "fail" if severities.get("FATAL", 0) or severities.get("ERROR", 0) else "warning" if severities.get("WARNING", 0) else "pass"
    return {
        "status": status,
        "score": round(score, 2),
        "counts": dict(severities),
        "issues": issues,
        "scene_count": len(scenes),
        "template_usage": dict(Counter(str(s.get("template")) for s in scenes)),
    }
