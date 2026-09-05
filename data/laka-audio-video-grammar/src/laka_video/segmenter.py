from __future__ import annotations

import re
from typing import Any

from .models import Cue, SceneDraft, TextUnit
from .utils import normalize_whitespace, word_count

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"“‘'])")
_CLAUSE_RE = re.compile(r"\s*(?:;|—|–|:\s+|,\s+(?=(?:but|and|so|while|instead|rather|then)\b))\s*", re.IGNORECASE)


def _weights(parts: list[str]) -> list[float]:
    return [max(1.0, word_count(p) + len(p) / 18.0) for p in parts]


def _timed_parts(parts: list[str], start: float, end: float) -> list[tuple[float, float, str]]:
    parts = [normalize_whitespace(p) for p in parts if normalize_whitespace(p)]
    if not parts:
        return []
    weights = _weights(parts)
    total = sum(weights)
    cursor = start
    result = []
    for i, (part, weight) in enumerate(zip(parts, weights)):
        t0 = cursor
        t1 = end if i == len(parts) - 1 else cursor + (end - start) * weight / total
        result.append((t0, t1, part))
        cursor = t1
    return result


def _split_long_part(text: str, start: float, end: float, max_seconds: float) -> list[tuple[float, float, str]]:
    duration = end - start
    if duration <= max_seconds:
        return [(start, end, text)]
    clauses = [p for p in _CLAUSE_RE.split(text) if normalize_whitespace(p)]
    if len(clauses) > 1:
        timed = _timed_parts(clauses, start, end)
        result: list[tuple[float, float, str]] = []
        for t0, t1, clause in timed:
            result.extend(_split_long_part(clause, t0, t1, max_seconds))
        return result
    tokens = text.split()
    pieces = max(2, int(round(duration / max_seconds + 0.499)))
    chunk_size = max(1, (len(tokens) + pieces - 1) // pieces)
    chunks = [" ".join(tokens[i:i + chunk_size]) for i in range(0, len(tokens), chunk_size)]
    return _timed_parts(chunks, start, end)


def cues_to_units(cues: list[Cue], config: dict[str, Any]) -> list[TextUnit]:
    """One unit per sentence.

    A scene is a sentence. Subtitle cues break wherever the transcriber's line
    ran out, which is not where a thought ends — a sentence routinely spans two
    cues, and splitting per cue turned one thought into two scenes. So the cues
    are stitched back into a continuous stream first, the stream is split at
    sentence boundaries, and each sentence is mapped back onto the time it was
    actually spoken.

    Only a sentence too long to sit in one scene is split further, at a clause
    boundary, because there is nothing else to do with it.
    """
    max_seconds = float(config.get("max_scene_seconds", 12.0))
    if not cues:
        return []

    # Stitch, remembering which characters belong to which cue's time span.
    spans: list[tuple[int, int, float, float, int]] = []
    buffer: list[str] = []
    cursor = 0
    for cue in cues:
        text = normalize_whitespace(cue.text)
        if not text:
            continue
        if buffer:
            buffer.append(" ")
            cursor += 1
        spans.append((cursor, cursor + len(text), cue.start, cue.end, cue.index))
        buffer.append(text)
        cursor += len(text)
    transcript = "".join(buffer)
    if not transcript:
        return []

    def time_at(position: int, edge: str) -> tuple[float, list[int]]:
        """Interpolate a character position back onto the spoken timeline."""
        for start, end, t0, t1, index in spans:
            if start <= position <= end:
                share = (position - start) / max(1, end - start)
                return t0 + (t1 - t0) * share, [index]
        if edge == "start":
            return spans[0][2], [spans[0][4]]
        return spans[-1][3], [spans[-1][4]]

    def cues_between(a: int, b: int) -> list[int]:
        return sorted({index for start, end, _, _, index in spans if start < b and end > a}) or [spans[0][4]]

    units: list[TextUnit] = []
    counter = 1
    position = 0
    for sentence in _SENTENCE_RE.split(transcript):
        clean = normalize_whitespace(sentence)
        if not clean:
            continue
        begin = transcript.find(sentence.strip(), position)
        if begin < 0:
            begin = position
        finish = begin + len(sentence.strip())
        position = finish
        start, _ = time_at(begin, "start")
        end, _ = time_at(finish, "end")
        if end <= start:
            end = start + 0.4
        ids = cues_between(begin, finish)
        tags: dict[str, Any] = {}
        for cue in cues:
            if cue.index in ids:
                tags.update(cue.tags)
        for p0, p1, part in _split_long_part(clean, start, end, max_seconds):
            units.append(TextUnit(
                id=f"unit-{counter:04d}", start=round(p0, 4), end=round(p1, 4),
                text=normalize_whitespace(part), cue_ids=ids, tags=dict(tags),
                explicit_boundary=True,
            ))
            counter += 1
    return units


def _combine_units(a: TextUnit, b: TextUnit, new_id: str) -> TextUnit:
    return TextUnit(
        id=new_id,
        start=min(a.start, b.start),
        end=max(a.end, b.end),
        text=normalize_whitespace(f"{a.text} {b.text}"),
        cue_ids=sorted(set(a.cue_ids + b.cue_ids)),
        tags={**a.tags, **b.tags},
        explicit_boundary=a.explicit_boundary or b.explicit_boundary,
    )


def units_to_scenes(units: list[TextUnit], config: dict[str, Any], duration: float) -> list[SceneDraft]:
    if not units:
        return []
    min_seconds = float(config.get("min_scene_seconds", 3.5))
    target = float(config.get("target_scene_seconds", 7.5))
    max_seconds = float(config.get("max_scene_seconds", 12.0))
    # The speaker's own pause is the argument boundary. Anything shorter than
    # this is continuous speech and belongs to one move.
    pause = float(config.get("pause_scene_boundary_seconds", 0.55))
    # No merging. cues_to_units already emits one unit per sentence, and a
    # scene is a sentence — joining two of them would join two thoughts.
    merged = list(units)

    drafts: list[SceneDraft] = []
    for idx, unit in enumerate(merged):
        start = unit.start
        end = unit.end
        if idx + 1 < len(merged):
            gap = merged[idx + 1].start - end
            if 0 < gap <= 1.25:
                end = merged[idx + 1].start
        elif duration > end:
            end = duration
        drafts.append(SceneDraft(
            id=f"scene-{idx + 1:03d}", start=round(start, 4), end=round(min(end, duration), 4),
            text=unit.text, cue_ids=unit.cue_ids, tags=dict(unit.tags),
        ))
    if drafts and drafts[0].start > 0:
        drafts[0].start = 0.0
    return drafts


def build_audio_only_scenes(duration: float, audio_summary: dict[str, Any], config: dict[str, Any], content: dict[str, Any]) -> list[SceneDraft]:
    min_seconds = float(config.get("min_scene_seconds", 3.5))
    target = float(config.get("target_scene_seconds", 7.5))
    max_seconds = float(config.get("max_scene_seconds", 12.0))
    candidates = [float(x) for x in audio_summary.get("section_boundaries", []) if 0 <= float(x) <= duration]
    candidates.extend([0.0, duration])
    candidates = sorted(set(round(x, 3) for x in candidates))
    boundaries = [0.0]
    cursor = 0.0
    while cursor < duration - 1e-6:
        viable = [b for b in candidates if cursor + min_seconds <= b <= cursor + max_seconds]
        if viable:
            nxt = min(viable, key=lambda b: abs((b - cursor) - target))
        else:
            nxt = min(duration, cursor + target)
        if duration - nxt < min_seconds * 0.55 and nxt < duration:
            nxt = duration
        if nxt <= cursor + 0.05:
            nxt = min(duration, cursor + target)
        boundaries.append(round(nxt, 4))
        cursor = nxt
    if boundaries[-1] < duration:
        boundaries.append(duration)

    chapters = content.get("chapters") or []
    title = content.get("title") or content.get("speaker") or "Audio presentation"
    scenes: list[SceneDraft] = []
    for i, (start, end) in enumerate(zip(boundaries, boundaries[1:])):
        if i == 0:
            text = str(title)
            tags = {"infographic": "title_card", "relation": "identity", "headline": str(title)}
        else:
            label = str(chapters[i - 1]) if i - 1 < len(chapters) else f"Section {i + 1:02d}"
            text = label
            tags = {"infographic": "audio_wave", "relation": "emphasis", "headline": label}
        scenes.append(SceneDraft(
            id=f"scene-{i + 1:03d}", start=start, end=end, text=text, cue_ids=[], tags=tags,
        ))
    return scenes
