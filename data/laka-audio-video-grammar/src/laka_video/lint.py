from __future__ import annotations

import math
from collections import Counter
from typing import Any

from .ordering import chunk_count, item_count, motion_events_for, scan_seconds, visible_words_for
from .utils import word_count


def _issue(severity: str, code: str, message: str, scene_id: str | None = None) -> dict[str, Any]:
    item = {"severity": severity, "code": code, "message": message}
    if scene_id:
        item["scene_id"] = scene_id
    return item


def _perception_checks(
    storyboard: dict[str, Any],
    perception: dict[str, Any],
    issues: list[dict[str, Any]],
) -> None:
    """Checks 1-16 per scene and 17-34 across the piece.

    Every threshold is read from grammar/perception.yml so a reviewer can see
    the number and its source rather than a literal buried in code.
    """
    scenes = storyboard.get("scenes", []) or []
    composition = storyboard.get("composition", {}) or {}
    width = float(composition.get("width", 1080))
    height = float(composition.get("height", 1920))
    unit = min(width, height) / float((perception.get("typography", {}) or {}).get("unit_divisor", 108))

    fixation = perception.get("fixation", {}) or {}
    memory = perception.get("working_memory", {}) or {}
    magnitude = perception.get("magnitude", {}) or {}
    motion_cfg = perception.get("motion", {}) or {}
    typography = perception.get("typography", {}) or {}
    accessibility = perception.get("accessibility", {}) or {}
    speech_cfg = perception.get("speech", {}) or {}
    reading_cfg = perception.get("reading", {}) or {}

    gate = float(fixation.get("duration_gate_ratio", 0.70))
    max_chunks = int(memory.get("max_simultaneous_marks", 4))
    max_motion = int(memory.get("max_concurrent_motion_events", 2))
    max_channels = int(memory.get("max_encoded_channels", 2))
    safe_channels = set(magnitude.get("quantity_safe_channels", []) or [])
    weber_floor = float(magnitude.get("min_drawable_difference", 0.05))
    share_max = float(speech_cfg.get("on_screen_share_max", 0.35))
    wps = float(reading_cfg.get("on_screen_words_per_second", 3.0))

    for scene in scenes:
        sid = str(scene.get("id"))
        template_id = str(scene.get("template"))
        payload = scene.get("payload", {}) or {}
        duration = max(0.01, float(scene.get("end", 0)) - float(scene.get("start", 0)))
        semantics = scene.get("semantics", {}) or {}

        visible = visible_words_for(template_id, payload)
        marks = int((scene.get("selection_trace", {}).get("selected", {}) or {}).get("order", {}).get("marks",
                    item_count(payload) + 2))
        required = scan_seconds(marks, visible, perception)

        # 1. readability gate. A scene carrying almost nothing that still fails
        #    is too SHORT, not too wordy, and saying "reduce the text" about a
        #    one-word frame is advice nobody can act on.
        ratio = required / duration
        if ratio > gate:
            floor_words = 3
            if visible <= floor_words:
                issues.append(_issue(
                    "INFO", "timing.too_short_to_read",
                    f"{duration:.1f}s cannot clear the gate even at {visible} word(s); "
                    f"the scene is too short, not too dense.", sid))
            else:
                issues.append(_issue(
                    "WARNING", "perception.readability",
                    f"Needs {required:.1f}s to read comfortably in a {duration:.1f}s scene "
                    f"(ratio {ratio:.2f} > {gate:.2f}); {visible} words on screen.", sid))

        # 2. working memory
        chunks = chunk_count(template_id, payload)
        if chunks > max_chunks:
            issues.append(_issue("WARNING", "perception.chunks",
                                 f"{chunks} simultaneous chunks exceeds the working-memory ceiling of {max_chunks}.", sid))

        # 3. concurrent motion
        events = motion_events_for(template_id, payload)
        if events > max_motion:
            issues.append(_issue("WARNING", "perception.motion_events",
                                 f"{events} concurrent motion events; a third competing motion destroys focus.", sid))

        # 4. encoded channels
        channels = 1 + (1 if payload.get("series") else 0) + (1 if payload.get("points") else 0)
        if channels > max_channels:
            issues.append(_issue("WARNING", "perception.channels",
                                 f"{channels} encoded channels forces a conjunction search.", sid))

        # 7 / 9. magnitude honesty
        from .ordering import QUANTITY_CHANNEL
        channel = QUANTITY_CHANNEL.get(template_id)
        asserts_quantity = bool(semantics.get("requires_numeric")) or bool(payload.get("series"))
        if asserts_quantity and channel and channel not in safe_channels and channel != "printed":
            issues.append(_issue("ERROR", "magnitude.unsafe_channel",
                                 f"{template_id} encodes a quantity by {channel}; Stevens' exponent makes that "
                                 f"channel systematically misread.", sid))

        # 8. Weber floor
        series = payload.get("series")
        if isinstance(series, list) and len(series) >= 2:
            try:
                values = sorted(float(item.get("value", 0)) for item in series if isinstance(item, dict))
                if values and values[-1] > 0 and (values[-1] - values[0]) / values[-1] < weber_floor:
                    issues.append(_issue("WARNING", "magnitude.below_weber_floor",
                                         f"Largest difference is under {weber_floor:.0%}; drawn as length it is "
                                         f"indistinguishable. Print the delta instead.", sid))
            except (TypeError, ValueError):
                pass

        # 21. label precision may not exceed claim precision
        if semantics.get("label_precision") == "rounded":
            number = str(payload.get("number", ""))
            if "." in number:
                issues.append(_issue("ERROR", "modality.false_precision",
                                     f"Claim is hedged but the label reads {number}.", sid))

        # 22 / 23. depiction gate
        depiction = str(semantics.get("depiction", "typography"))
        has_asset = bool(scene.get("asset") or payload.get("asset"))
        if has_asset and depiction != "photograph":
            issues.append(_issue("WARNING", "depiction.too_literal",
                                 f"Head noun is {semantics.get('concreteness_band')}; a photograph is not licensed.", sid))

        # 24. unfilled roles must stay unfilled
        for role in semantics.get("unfilled_core_roles", []) or []:
            issues.append(_issue("INFO", "frame.role_unfilled",
                                 f"Frame role '{role}' was not stated; no mark may stand in for it.", sid))

        # 25. motion operator matches aspect
        operator = str(semantics.get("motion_operator", ""))
        family = str((scene.get("motion", {}) or {}).get("family", ""))
        if operator == "static" and family in {"trace", "accumulate"}:
            issues.append(_issue("INFO", "aspect.motion_mismatch",
                                 f"Stative claim rendered with a {family} build.", sid))

        # 26. negation shows the object first
        negation = semantics.get("negation")
        if negation and not negation.get("show_positive_first", True):
            issues.append(_issue("WARNING", "negation.absence_only",
                                 "Negation must show the object and then strike it, never only its absence.", sid))

        # 30. headline must not duplicate the concurrent caption
        headline = str(payload.get("headline", "")).strip().lower()
        if headline:
            for caption in storyboard.get("captions", []) or []:
                if float(caption.get("t0", 0)) >= float(scene.get("start", 0)) and \
                   float(caption.get("t1", 0)) <= float(scene.get("end", 0)):
                    if str(caption.get("text", "")).strip().lower() in headline:
                        issues.append(_issue("INFO", "redundancy.caption_headline",
                                             "Headline repeats the caption on screen at the same moment.", sid))
                        break

        # §1.4 on-screen words are a fraction of spoken words
        spoken = word_count(str(scene.get("text", "")))
        if spoken and visible / spoken > share_max:
            issues.append(_issue("INFO", "perception.transcription",
                                 f"{visible} of {spoken} spoken words are on screen "
                                 f"({visible / spoken:.0%} > {share_max:.0%}); the frame is transcribing, not composing.", sid))

    # ---- composition level, checks 17-20 ---------------------------------
    report = storyboard.get("composition_report", {}) or {}
    if report:
        if report.get("accent_bleed_scenes", 0) > report.get("accent_budget", 1):
            issues.append(_issue("WARNING", "rhythm.accent_budget",
                                 f"{report['accent_bleed_scenes']} full-bleed accent scenes; the budget is "
                                 f"{report['accent_budget']} at the conversion moment."))
        if not report.get("carrier_persistence_met", True):
            actual = report.get("carrier_persistence", 0)
            possible = report.get("carrier_opportunities", 0)
            target = report.get("carrier_persistence_min", 0.4)
            if possible > actual + 0.05:
                issues.append(_issue("WARNING", "rhythm.carrier_persistence",
                                     f"{actual:.0%} of scenes evolve an existing object where {possible:.0%} could "
                                     f"have without dropping an obligation (target {target:.0%})."))
            else:
                issues.append(_issue("INFO", "rhythm.carrier_material",
                                     f"{actual:.0%} of scenes evolve an existing object against a {target:.0%} "
                                     f"target, and only {possible:.0%} of cuts could without weakening a claim. "
                                     f"The source changes subject and shape almost every scene; persistence would "
                                     f"have to come from the edit, not the compiler."))
        if not report.get("scene_count_in_band", True):
            issues.append(_issue("INFO", "rhythm.scene_count",
                                 f"{report.get('scene_count')} scenes against an expected "
                                 f"{report.get('expected_scene_count')}; scenes should be argument moves, not sentences."))
    previous_level = None
    for scene in scenes:
        level = scene.get("density_level")
        if level == "D3" and previous_level == "D3":
            issues.append(_issue("WARNING", "rhythm.consecutive_density",
                                 "Two maximum-density scenes in a row.", str(scene.get("id"))))
        previous_level = level


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

    perception = storyboard.get("perception") or {}
    if perception:
        _perception_checks(storyboard, perception, issues)

    severities = Counter(issue["severity"] for issue in issues)
    # Deductions are per-scene-normalised so the score reads the same on a
    # 5-scene demo and a 29-scene film. A flat per-issue deduction pinned every
    # long piece to zero once the perception checks landed, which destroyed the
    # signal the number exists to carry.
    scale = max(1.0, len(scenes) / 5.0)
    deductions = (
        severities.get("FATAL", 0) * 30
        + severities.get("ERROR", 0) * 8
        + severities.get("WARNING", 0) * 2.5 / scale
        + severities.get("INFO", 0) * 0.5 / scale
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
