from __future__ import annotations

from typing import Any

from .models import Cue
from .utils import normalize_whitespace


def _word_weight(word: str) -> float:
    clean = "".join(ch for ch in word if ch.isalnum() or ch in "’'-")
    return len(clean) + 1.6


def build_captions(cues: list[Cue], config: dict[str, Any]) -> list[dict[str, Any]]:
    max_words = int(config.get("max_caption_words", 7))
    max_chars = int(config.get("max_caption_characters", 34))
    chunks: list[dict[str, Any]] = []
    for cue in cues:
        tokens = cue.text.split()
        if not tokens:
            continue
        weights = [_word_weight(w) for w in tokens]
        total = max(sum(weights), 1e-6)
        cursor = cue.start
        timed_words = []
        for token, weight in zip(tokens, weights):
            t0 = cursor
            cursor += cue.duration * weight / total
            timed_words.append({"w": token, "t0": round(t0, 4), "t1": round(cursor, 4)})
        current: list[dict[str, Any]] = []
        length = 0
        for word in timed_words:
            projected = length + len(word["w"]) + (1 if current else 0)
            if current and (len(current) >= max_words or projected > max_chars):
                chunks.append({
                    "t0": current[0]["t0"],
                    "t1": current[-1]["t1"],
                    "text": normalize_whitespace(" ".join(w["w"] for w in current)),
                    "words": current,
                    "cue_id": cue.index,
                    "alignment": "estimated_by_word_weight",
                })
                current = []
                length = 0
            current.append(word)
            length += len(word["w"]) + (1 if len(current) > 1 else 0)
        if current:
            chunks.append({
                "t0": current[0]["t0"],
                "t1": current[-1]["t1"],
                "text": normalize_whitespace(" ".join(w["w"] for w in current)),
                "words": current,
                "cue_id": cue.index,
                "alignment": "estimated_by_word_weight",
            })
    return chunks
