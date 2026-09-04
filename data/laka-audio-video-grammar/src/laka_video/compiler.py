from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

from jsonschema import validate

from . import __version__
from .audio import AudioAnalysis, analyze_audio
from .budget import fit_payload_to_budget
from .captions import build_captions
from .html_renderer import render_preview
from .composition import apply_composition
from .lint import lint_storyboard
from .motion import compile_motion
from .report import decision_report
from .segmenter import build_audio_only_scenes, cues_to_units, units_to_scenes
from .selector import TemplateSelector
from .semantics import analyze as analyze_semantics, load_lexicon
from .srt import parse_srt
from .studio import load_studio_library
from .text_rules import TextRuleEngine
from .utils import (
    deep_merge,
    default_grammar_dir,
    json_safe,
    load_yaml,
    normalize_whitespace,
    resolve_path,
    word_count,
    words,
    write_json,
)


def _load_structured(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    if not path.exists():
        raise FileNotFoundError(f"Structured input not found: {path}")
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return load_yaml(path)


def _aspect_dimensions(aspect: str) -> tuple[int, int]:
    return {
        "9:16": (1080, 1920),
        "16:9": (1920, 1080),
        "1:1": (1080, 1080),
        "4:5": (1080, 1350),
    }.get(aspect, (1080, 1920))


def _relative_reference(path: Path | None, base: Path) -> str | None:
    if path is None:
        return None
    try:
        return Path(os.path.relpath(path, base)).as_posix()
    except ValueError:
        return str(path)


def _scene_override(scene: Any, override_doc: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in override_doc.get("overrides", []) if isinstance(override_doc, dict) else []:
        if not isinstance(item, dict):
            continue
        matched = False
        if item.get("scene") == scene.id:
            matched = True
        cue = item.get("cue")
        if cue is not None and int(cue) in scene.cue_ids:
            matched = True
        interval = item.get("time")
        if isinstance(interval, list) and len(interval) == 2:
            a, b = float(interval[0]), float(interval[1])
            if scene.start < b and scene.end > a:
                matched = True
        phrase = item.get("text")
        if phrase and str(phrase).lower() in scene.text.lower():
            matched = True
        if matched:
            result.update({k: v for k, v in item.items() if k not in {"scene", "cue", "time", "text"}})
    return result


def _continuity_key(text: str, payload: dict[str, Any], stopwords: set[str]) -> str:
    for key in ("term", "center", "parent", "headline"):
        value = payload.get(key)
        if isinstance(value, str):
            candidates = [w.lower() for w in words(value) if w.lower() not in stopwords and len(w) > 3]
            if candidates:
                return candidates[0]
    candidates = [w.lower() for w in words(text) if w.lower() not in stopwords and len(w) > 3]
    return candidates[0] if candidates else "scene"


def _local_energy_bars(audio: AudioAnalysis, start: float, end: float, count: int = 48) -> list[float]:
    mask = (audio.frame_times >= start) & (audio.frame_times < end)
    values = audio.rms_normalized[mask]
    if values.size == 0:
        return [0.0] * count
    import numpy as np
    edges = np.linspace(0, values.size, count + 1).astype(int)
    output: list[float] = []
    for i in range(count):
        chunk = values[edges[i]:max(edges[i] + 1, edges[i + 1])]
        output.append(round(float(chunk.mean()) if chunk.size else 0.0, 4))
    return output



# Frame role slot -> payload key. Only ever fills a gap; an extraction the text
# pass already made always wins, because it was made with more context.
_ROLE_SLOT_TO_PAYLOAD = {
    "left": "left",
    "right": "right",
    "centre": "center",
    "boundary": "parent",
    "hero_mark": "number",
    "entity_label": "label",
    "axis_label": "unit",
}


def _fill_payload_from_roles(payload: dict[str, Any], semantics: Any) -> None:
    roles = getattr(semantics, "roles", None) or {}
    if not roles:
        return
    from .semantics.lexicon import load_lexicon as _load_lex

    frame_id = getattr(semantics, "frame", None)
    if not frame_id:
        return
    lex = _load_lex()
    frame = next((f for f in lex.frames if f.id == frame_id), None)
    if frame is None:
        return
    for role_name, span in roles.items():
        slot = (frame.roles.get(role_name) or {}).get("slot")
        key = _ROLE_SLOT_TO_PAYLOAD.get(str(slot))
        if not key or payload.get(key):
            continue
        text = str(span).strip()
        if text and len(text.split()) <= 9:
            payload[key] = text
    # A pair is only a pair when both halves are present.
    if bool(payload.get("left")) != bool(payload.get("right")):
        payload.pop("left", None)
        payload.pop("right", None)

def compile_project(project_path: str | Path, grammar_dir: str | Path | None = None) -> dict[str, Path]:
    project_file = Path(project_path).expanduser().resolve()
    if not project_file.exists():
        raise FileNotFoundError(f"Project file not found: {project_file}")
    base_dir = project_file.parent
    grammar = Path(grammar_dir).resolve() if grammar_dir else default_grammar_dir()

    project_doc = load_yaml(project_file)
    project_schema = json.loads((grammar / "project.schema.json").read_text(encoding="utf-8"))
    storyboard_schema = json.loads((grammar / "storyboard.schema.json").read_text(encoding="utf-8"))
    validate(project_doc, project_schema)

    defaults = load_yaml(grammar / "defaults.yml")
    lexicon = load_yaml(grammar / "lexicon.yml")
    template_library = load_yaml(grammar / "templates.yml")
    studio_library = load_studio_library(grammar)
    motion_library = load_yaml(grammar / "motion.yml")
    # Published perceptual thresholds. Every gate in the selector and the linter
    # reads its numbers from here rather than carrying a literal.
    perception = load_yaml(grammar / "perception.yml")

    timing_cfg = deep_merge(defaults.get("timing", {}), project_doc.get("rules", {}))
    text_cfg = deep_merge(defaults.get("text", {}), project_doc.get("rules", {}))
    selection_cfg = deep_merge(defaults.get("selection", {}), project_doc.get("selection", {}))
    audio_cfg = deep_merge(defaults.get("audio", {}), project_doc.get("audio", {}))
    output_cfg = deep_merge(defaults.get("output", {}), project_doc.get("output", {}))
    defaults_runtime = deep_merge(defaults, {
        "timing": timing_cfg,
        "text": text_cfg,
        "selection": selection_cfg,
        "audio": audio_cfg,
        "output": output_cfg,
    })
    flat_scene_cfg = {**timing_cfg, **text_cfg}

    source = project_doc.get("source", {})
    audio_path = resolve_path(base_dir, source.get("audio"))
    transcript_path = resolve_path(base_dir, source.get("transcript"))
    music_path = resolve_path(base_dir, source.get("music"))
    overrides_path = resolve_path(base_dir, source.get("overrides"))
    data_path = resolve_path(base_dir, source.get("data"))
    if audio_path is None:
        raise ValueError("source.audio is required")

    audio = analyze_audio(audio_path, audio_cfg)
    mode = str(source.get("mode", "auto"))
    if mode == "auto":
        mode = "transcript" if transcript_path else "audio"
    if mode in {"transcript", "directed"} and transcript_path is None:
        raise ValueError(f"Mode {mode} requires source.transcript")

    brand_block = project_doc.get("brand", {}) or {}
    brand_path = resolve_path(base_dir, brand_block.get("preset")) if brand_block.get("preset") else grammar / "brand.example.yml"
    brand = deep_merge(load_yaml(brand_path), {k: v for k, v in brand_block.items() if k != "preset"})

    project_output = project_doc.get("output", {}) or {}
    aspect = str(output_cfg.get("aspect", "9:16"))
    default_width, default_height = _aspect_dimensions(aspect)
    # Global defaults describe the default aspect only. They must not override
    # the dimensions implied by a project's selected aspect ratio.
    width = int(project_output.get("width") or default_width)
    height = int(project_output.get("height") or default_height)
    fps = float(output_cfg.get("fps", 30))
    tail = float(output_cfg.get("tail_seconds", timing_cfg.get("tail_seconds", 2.0)))
    composition_duration = round(audio.duration + tail, 4)
    output_dir = resolve_path(base_dir, str(output_cfg.get("directory", "build")))
    assert output_dir is not None

    content = project_doc.get("content", {}) or {}
    cues = parse_srt(transcript_path) if transcript_path else []
    if cues:
        units = cues_to_units(cues, flat_scene_cfg)
        drafts = units_to_scenes(units, flat_scene_cfg, audio.duration)
    else:
        drafts = build_audio_only_scenes(audio.duration, audio.public_summary(), flat_scene_cfg, {**content, "title": project_doc.get("project", {}).get("title")})
    if drafts:
        drafts[-1].end = composition_duration

    override_doc = _load_structured(overrides_path)
    data_doc = _load_structured(data_path)
    text_engine = TextRuleEngine(lexicon)
    semantic_lexicon = load_lexicon(str(grammar))
    selector = TemplateSelector(template_library, defaults_runtime, brand, studio_library, perception)
    history: list[dict[str, Any]] = []
    compiled_scenes: list[dict[str, Any]] = []
    seed = project_doc.get("project", {}).get("seed", 0)
    composition_mode = str((project_doc.get("composition") or {}).get("mode", "studio"))

    for draft in drafts:
        sidecar_override = _scene_override(draft, override_doc)
        overrides = {**draft.tags, **sidecar_override}
        analysis = text_engine.classify(draft.text, overrides)
        # The linguistic pass: relation, role structure, aspect, modality,
        # depiction licence. It never picks a template on its own — it supplies
        # the evidence the selector orders candidates by.
        semantics = analyze_semantics(draft.text, semantic_lexicon)
        analysis["semantics"] = semantics
        # Frame roles are evidence the sentence supplied. Where the text pass
        # left a slot empty, the frame fills it — otherwise the analysis reports
        # an obligation no template can satisfy and every candidate is charged
        # for dropping content that was never handed to it.
        _fill_payload_from_roles(analysis["payload"], semantics)
        # The scene's duration bounds what it can carry, before any template is
        # chosen. Over budget, drop a density level rather than shrink the type.
        budget_record = fit_payload_to_budget(
            analysis["payload"], draft.text, max(0.01, draft.duration), perception
        )
        data_bound = False
        data_key = overrides.get("data")
        if data_key and isinstance(data_doc, dict):
            block = data_doc.get("data", data_doc).get(str(data_key))
            if isinstance(block, dict):
                analysis["payload"].update(block)
                data_bound = True
        features = audio.interval_features(draft.start, min(draft.end, audio.duration))
        if mode == "audio" or overrides.get("infographic") == "audio_wave":
            analysis["payload"]["energy_bars"] = _local_energy_bars(audio, draft.start, min(draft.end, audio.duration))
            analysis["payload"]["tempo_bpm"] = audio.summary.get("tempo_bpm")
            analysis["payload"]["section_index"] = len(compiled_scenes) + 1
        scene_info = {
            "id": draft.id,
            "start": draft.start,
            "end": draft.end,
            "words_per_second": round(word_count(draft.text) / max(draft.duration, 0.25), 4),
            "audio_features": features,
        }
        continuity_key = _continuity_key(draft.text, analysis["payload"], text_engine.stopwords)
        scene_info["continuity_key"] = continuity_key
        selected, candidates = selector.select(
            analysis=analysis,
            scene=scene_info,
            output={**output_cfg, "aspect": aspect},
            history=history,
            seed=seed,
            overrides=overrides,
            context={
                "data_bound": data_bound,
                "selection_mode": composition_mode,
                "semantics": semantics,
            },
        )
        template_spec = selector.by_id.get(selected.template, {})
        motion = compile_motion(
            motion_library,
            template_spec.get("motion_family", "reveal"),
            analysis,
            scene_info,
            defaults_runtime,
            brand,
            overrides,
        )
        scene_record = {
            "id": draft.id,
            "start": round(draft.start, 4),
            "end": round(draft.end, 4),
            "duration": round(draft.duration, 4),
            "cue_ids": draft.cue_ids,
            "text": draft.text,
            "speech_act": analysis["speech_act"],
            "automatic_relation": analysis["automatic_relation"],
            "primary_relation": analysis["primary_relation"],
            "relation_scores": analysis["relation_scores"],
            "relation_evidence": analysis["evidence"],
            "sensitive": analysis["sensitive"],
            "continuity_key": continuity_key,
            "semantics": semantics.to_dict(),
            "reading_budget": budget_record,
            "words_per_second": scene_info["words_per_second"],
            "audio_features": features,
            "template": selected.template,
            "layout": selected.layout,
            "density": str(overrides.get("density") or template_spec.get("density", "low")),
            "payload": analysis["payload"],
            "motion": motion,
            "asset": overrides.get("asset"),
            "data_bound": data_bound,
            "overrides": overrides,
            "selection_trace": {
                "selected": selected.to_dict(),
                "candidates": [c.to_dict() for c in sorted(candidates, key=lambda x: -x.score)[:8]],
            },
        }
        if draft.duration < timing_cfg.get("min_scene_seconds", 3.5) and len(draft.text.split()) <= 3:
            scene_record["allow_short_scene"] = True
        compiled_scenes.append(scene_record)
        history.append({"template": selected.template, "layout": selected.layout, "continuity_key": continuity_key})

    captions = build_captions(cues, text_cfg) if cues and output_cfg.get("captions", "karaoke") != "none" else []
    storyboard = {
        "engine_version": __version__,
        "grammar_version": defaults.get("version", "1.0.0"),
        "project": project_doc.get("project", {}),
        "source": {
            "mode": mode,
            "audio_original": _relative_reference(audio_path, output_dir),
            "transcript_original": _relative_reference(transcript_path, output_dir),
            "music_original": _relative_reference(music_path, output_dir),
        },
        "composition": {
            "duration": composition_duration,
            "audio_duration": round(audio.duration, 4),
            "tail_seconds": tail,
            "width": width,
            "height": height,
            "fps": fps,
            "aspect": aspect,
            "captions": output_cfg.get("captions", "karaoke"),
            "selection_mode": composition_mode,
        },
        "studio": {
            "library": studio_library.get("name", "LAVC Studio Library"),
            "library_version": studio_library.get("version", "1.0.0"),
            "principle": studio_library.get("principle", ""),
            "mode": composition_mode,
            "seed": seed,
        },
        "content": content,
        "brand": brand,
        "perception": perception,
        "audio_analysis": audio.public_summary(),
        "captions": captions,
        "scenes": compiled_scenes,
        "film": {
            "engine": "cue-film-v1",
            "scenes": [
                {
                    "name": "Opening" if index == 0 else "Close" if index == len(compiled_scenes) - 1 else f"{scene['primary_relation'].replace('_', ' ').title()} {index + 1:02d}",
                    "at": scene["start"],
                    "dur": scene["duration"],
                    "desc": scene["payload"].get("headline") or scene["text"],
                }
                for index, scene in enumerate(compiled_scenes)
            ],
            "caps": [
                {"at": cue.start, "until": cue.end, "text": cue.text}
                for cue in cues
            ],
        },
    }
    # Rhythm, accent budget, carrier persistence and the ending are properties
    # of the whole piece, so they are enforced after every scene is chosen.
    storyboard["composition_report"] = apply_composition(
        compiled_scenes, perception, float(composition_duration)
    )
    storyboard = json_safe(storyboard)
    report = lint_storyboard(storyboard, defaults_runtime, template_library)
    storyboard["lint_summary"] = {k: v for k, v in report.items() if k != "issues"}
    validate(storyboard, storyboard_schema)

    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    copy_media = bool(output_cfg.get("copy_media", True))
    if copy_media:
        audio_target = assets_dir / f"audio{audio_path.suffix.lower()}"
        shutil.copy2(audio_path, audio_target)
        audio_src = f"assets/{audio_target.name}"
        music_src = None
        if music_path:
            music_target = assets_dir / f"music{music_path.suffix.lower()}"
            shutil.copy2(music_path, music_target)
            music_src = f"assets/{music_target.name}"
    else:
        # Keep previews portable when media remains beside the project instead of being copied.
        # Relative browser paths survive moving or zipping the whole project directory.
        try:
            audio_src = Path(os.path.relpath(audio_path, output_dir)).as_posix()
        except ValueError:
            audio_src = audio_path.as_uri()
        if music_path:
            try:
                music_src = Path(os.path.relpath(music_path, output_dir)).as_posix()
            except ValueError:
                music_src = music_path.as_uri()
        else:
            music_src = None

    storyboard_path = output_dir / "storyboard.json"
    report_path = output_dir / "lint-report.json"
    decision_path = output_dir / "decision-report.md"
    preview_path = output_dir / "preview.html"
    write_json(storyboard_path, storyboard)
    write_json(report_path, report)
    decision_path.write_text(decision_report(storyboard), encoding="utf-8")
    render_preview(storyboard, preview_path, audio_src=audio_src, music_src=music_src)
    return {
        "storyboard": storyboard_path,
        "preview": preview_path,
        "lint": report_path,
        "decisions": decision_path,
        "output_dir": output_dir,
    }
