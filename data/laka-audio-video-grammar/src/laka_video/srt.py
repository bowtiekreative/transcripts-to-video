from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any

from .models import Cue
from .utils import normalize_whitespace, parse_scalar

_TAG_RE = re.compile(r"\[\[\s*LAKA\s+(.+?)\]\]", flags=re.IGNORECASE | re.DOTALL)
_TIME_RE = re.compile(
    r"(?P<h1>\d{1,2}):(?P<m1>\d{2}):(?P<s1>\d{2})[,.](?P<ms1>\d{3})\s*-->\s*"
    r"(?P<h2>\d{1,2}):(?P<m2>\d{2}):(?P<s2>\d{2})[,.](?P<ms2>\d{3})"
)


def _seconds(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def parse_tag_body(body: str) -> dict[str, Any]:
    # Semicolons are accepted as visual separators outside quoted strings.
    normalized = body.replace(";", " ")
    try:
        tokens = shlex.split(normalized)
    except ValueError:
        tokens = normalized.split()
    result: dict[str, Any] = {}
    for token in tokens:
        if "=" not in token:
            result[token.strip()] = True
            continue
        key, value = token.split("=", 1)
        result[key.strip().lower()] = parse_scalar(value.strip())
    return result


def extract_laka_tags(text: str) -> tuple[str, dict[str, Any]]:
    tags: dict[str, Any] = {}
    for match in _TAG_RE.finditer(text or ""):
        tags.update(parse_tag_body(match.group(1)))
    clean = _TAG_RE.sub(" ", text or "")
    return normalize_whitespace(clean), tags


def parse_srt(path: str | Path) -> list[Cue]:
    raw = Path(path).read_text(encoding="utf-8-sig")
    blocks = re.split(r"\n\s*\n", raw.replace("\r\n", "\n").replace("\r", "\n").strip())
    cues: list[Cue] = []
    fallback_index = 1
    for block in blocks:
        lines = [line.rstrip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        time_line_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if time_line_index is None:
            continue
        match = _TIME_RE.search(lines[time_line_index])
        if not match:
            continue
        try:
            index = int(lines[0]) if time_line_index > 0 else fallback_index
        except ValueError:
            index = fallback_index
        gd = match.groupdict()
        start = _seconds(gd["h1"], gd["m1"], gd["s1"], gd["ms1"])
        end = _seconds(gd["h2"], gd["m2"], gd["s2"], gd["ms2"])
        text = " ".join(lines[time_line_index + 1 :])
        clean, tags = extract_laka_tags(text)
        if clean and end > start:
            cues.append(Cue(index=index, start=start, end=end, text=clean, tags=tags))
            fallback_index = index + 1
    cues.sort(key=lambda c: (c.start, c.index))
    return cues
