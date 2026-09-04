from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MOTION_VARIABLES = (
    "magnitude", "rate", "direction", "scope", "depth", "duration", "frequency",
    "acceleration", "variability", "detectability", "reversibility", "propagation",
    "amplification", "accumulation",
)


def _escape(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def _time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    minutes = int(seconds // 60)
    remainder = seconds - minutes * 60
    return f"{minutes:02d}:{remainder:05.2f}"


def _compact_payload(payload: dict[str, Any]) -> str:
    preferred = ("number", "label", "term", "definition", "left", "right", "items", "events", "nodes")
    pieces: list[str] = []
    for key in preferred:
        value = payload.get(key)
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            shown = value[:4]
            text = "; ".join(_escape(v.get("event", v) if isinstance(v, dict) else v) for v in shown)
            if len(value) > len(shown):
                text += f"; +{len(value)-len(shown)} more"
        else:
            text = _escape(value)
        pieces.append(f"**{key}:** {text}")
    return " · ".join(pieces) or "No structured payload; exact source text is used."


def decision_report(storyboard: dict[str, Any]) -> str:
    project = storyboard.get("project", {})
    comp = storyboard.get("composition", {})
    scenes = storyboard.get("scenes", [])
    lines: list[str] = [
        f"# LAVC decision report — {_escape(project.get('title', 'Untitled'))}",
        "",
        "This report records the deterministic choices used to compile the presentation. "
        "It is an audit trail, not an AI explanation.",
        "",
        "## Composition",
        "",
        f"- Project ID: `{_escape(project.get('id', ''))}`",
        f"- Duration: `{float(comp.get('duration', 0)):.3f}s`",
        f"- Canvas: `{comp.get('width', '')} × {comp.get('height', '')}`",
        f"- Aspect: `{_escape(comp.get('aspect', ''))}`",
        f"- Frame rate: `{_escape(comp.get('fps', ''))}`",
        f"- Scenes: `{len(scenes)}`",
        f"- Studio library: `{_escape(storyboard.get('studio', {}).get('library_version', ''))}`",
        f"- Selection mode: `{_escape(storyboard.get('studio', {}).get('mode', comp.get('selection_mode', '')))}`",
        f"- Selection seed: `{_escape(storyboard.get('studio', {}).get('seed', ''))}`",
        "",
        "## Scene map",
        "",
        "| # | Time | Detected relation | Infographic | Layout | Motion |",
        "|---:|---|---|---|---|---|",
    ]
    for index, scene in enumerate(scenes, 1):
        lines.append(
            f"| {index} | {_time(scene.get('start', 0))}–{_time(scene.get('end', 0))} | "
            f"{_escape(scene.get('primary_relation'))} | {_escape(scene.get('template'))} | "
            f"{_escape(scene.get('layout'))} | {_escape(scene.get('motion', {}).get('family'))} |"
        )

    for index, scene in enumerate(scenes, 1):
        trace = scene.get("selection_trace", {})
        selected = trace.get("selected", {})
        candidates = trace.get("candidates", [])[:3]
        motion = scene.get("motion", {})
        lines.extend([
            "",
            f"## {index:02d}. `{_escape(scene.get('id'))}` — {_time(scene.get('start', 0))} to {_time(scene.get('end', 0))}",
            "",
            f"> {_escape(scene.get('text', ''))}",
            "",
            f"**Relation:** `{_escape(scene.get('primary_relation'))}` "
            f"(automatic: `{_escape(scene.get('automatic_relation'))}`)",
            "",
            f"**Payload:** {_compact_payload(scene.get('payload', {}))}",
            "",
            f"**Selected:** `{_escape(scene.get('template'))}` / `{_escape(scene.get('layout'))}` "
            f"at score `{float(selected.get('score', 0)):.2f}`.",
            "",
        ])
        if scene.get("asset"):
            lines.extend([
                f"**Image slot:** filled from `{_escape(scene.get('overrides', {}).get('asset_source', scene.get('asset')))}`.",
                "",
            ])
        if candidates:
            lines.extend([
                "Top candidates:",
                "",
                "| Candidate | Layout | Score | Main evidence | Penalties |",
                "|---|---|---:|---|---|",
            ])
            for candidate in candidates:
                positive = candidate.get("positive", {})
                evidence = ", ".join(
                    f"{k}={float(v):.1f}" for k, v in sorted(positive.items(), key=lambda kv: -float(kv[1]))[:4]
                )
                penalties = candidate.get("penalties", {})
                penalty_text = ", ".join(f"{k}={float(v):.1f}" for k, v in penalties.items()) or "none"
                lines.append(
                    f"| {_escape(candidate.get('template'))} | {_escape(candidate.get('layout'))} | "
                    f"{float(candidate.get('score', 0)):.2f} | {_escape(evidence)} | {_escape(penalty_text)} |"
                )

        lines.extend([
            "",
            "LAKA motion volume:",
            "",
            "| Variable | State |",
            "|---|---|",
        ])
        for variable in MOTION_VARIABLES:
            lines.append(f"| {variable} | {_escape(motion.get(variable, ''))} |")
        mechanisms = ", ".join(str(x) for x in motion.get("mechanisms", [])) or "none"
        modifiers = ", ".join(str(x) for x in motion.get("applied_modifiers", [])) or "none"
        lines.extend([
            "",
            f"Mechanisms: `{_escape(mechanisms)}`. Applied modifiers: `{_escape(modifiers)}`.",
        ])

    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        "Acoustic features determine timing, silence, energy, onset density, and motion intensity. "
        "Semantic infographic selection comes from literal transcript patterns, supplied data, or author tags. "
        "The compiler never invents a statistic, hierarchy, causal link, comparison, or timeline event.",
        "",
    ])
    return "\n".join(lines)


def write_decision_report(storyboard_path: str | Path, output_path: str | Path | None = None) -> Path:
    source = Path(storyboard_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Storyboard not found: {source}")
    data = json.loads(source.read_text(encoding="utf-8"))
    output = Path(output_path).expanduser().resolve() if output_path else source.parent / "decision-report.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(decision_report(data), encoding="utf-8")
    return output
