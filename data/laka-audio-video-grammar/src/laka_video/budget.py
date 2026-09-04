"""Fit the payload to the scene's time budget (MOTION_MATH.md §1.3, §1.4).

A scene has a fixed duration, so the words it can carry are bounded before any
template is chosen:

    t_read_available = 0.70 * duration - t_orient - t_scan - t_hold
    max_words        = t_read_available * on_screen_words_per_second

and independently, on-screen words are a FRACTION of spoken words (25-35%),
never a transcript of them. A frame that shows every word the narrator says is
not a graphic, it is a teleprompter, and it fails the redundancy principle
while it fails the clock.

When the payload exceeds the budget the answer is to drop a density level, not
to shrink the type: fewer items, a shorter headline, supporting copy withdrawn.
Every removal is recorded on the scene so the decision report can show it.
"""
from __future__ import annotations

import math
from typing import Any

from .ordering import visible_words_for
from .text_rules import _trim_trailing_function_words
from .utils import word_count


def _headline_trim(text: str, max_words: int) -> str:
    """Cut at a clause boundary, or not at all.

    The reading budget is a warning; a headline reading "I'm a cognitive" is a
    defect. If no cut leaves a grammatical phrase, the original is returned and
    the scene goes over budget — which the linter will say plainly, rather than
    the frame saying something broken.
    """
    source = str(text or "")
    tokens = source.split()
    if len(tokens) <= max_words:
        return source

    window = " ".join(tokens[:max_words])
    for separator in (";", ":", ",", " and ", " but ", " so ", " because ", " that ", " which ", " when "):
        head, found, _ = window.rpartition(separator)
        candidate = _trim_trailing_function_words(head)
        if found and word_count(candidate) >= 3:
            return candidate

    # No clause boundary inside the window. Without a parser there is no way to
    # tell "You might know" from a finished phrase, so nothing is cut. The
    # headline arrived from _headline_span already cut at a boundary; cutting it
    # again on word count alone is how "I'm a cognitive architect" became
    # "I'm a cognitive".
    return source


def fit_payload_to_budget(
    payload: dict[str, Any],
    text: str,
    duration: float,
    perception: dict[str, Any],
) -> dict[str, Any]:
    """Trim in place. Returns an audit record of what was removed and why."""
    fixation = perception.get("fixation", {}) or {}
    reading = perception.get("reading", {}) or {}
    speech = perception.get("speech", {}) or {}

    gate = float(fixation.get("duration_gate_ratio", 0.70))
    orient = float(fixation.get("orient_seconds", 0.35))
    scan_base = float(fixation.get("scan_base_seconds", 0.30))
    scan_coef = float(fixation.get("scan_log_coefficient", 0.15))
    hold = float(fixation.get("hold_seconds", 0.60))
    wps = float(reading.get("on_screen_words_per_second", 3.0))
    share_max = float(speech.get("on_screen_share_max", 0.35))

    spoken = word_count(text)
    removals: list[str] = []

    def marks_now() -> int:
        count = 2
        for key in ("items", "nodes", "children", "series", "events"):
            value = payload.get(key)
            if isinstance(value, list):
                count += len(value)
                break
        return count

    def budget() -> int:
        """The clock is the hard constraint.

        The 25-35% speech share is a composition target, not a perceptual
        limit, so it is reported rather than enforced: trimming to it would
        shred sentences to satisfy a ratio, and a frame that says too little is
        the other half of the MDL failure.
        """
        scan = scan_base + scan_coef * math.log2(max(1, marks_now()) + 1)
        available = gate * duration - orient - scan - hold
        return max(3, int(available * wps))

    def visible() -> int:
        # Measured against the templates this payload could actually reach, so
        # the budget is not set by fields no frame will ever render together.
        candidates = [t for t in ("before_after", "list_stack", "big_number", "title_card")]
        return max(visible_words_for(t, payload) for t in candidates)

    allowed = budget()
    before = visible()

    # 1. Supporting copy is the first thing to go: the narrator is already
    #    saying it, and the redundancy principle says the duplicate costs more
    #    than it carries.
    if visible() > allowed and payload.get("supporting"):
        payload.pop("supporting", None)
        removals.append("supporting copy withdrawn (narration carries it)")

    # 2. Then list length. Dropping the tail of a list is a density-ladder step
    #    down, and the ladder is ordered so this happens before type shrinks.
    for key in ("items", "nodes", "children", "events"):
        value = payload.get(key)
        if not isinstance(value, list) or len(value) <= 2:
            continue
        while len(payload[key]) > 2 and visible() > allowed:
            payload[key] = payload[key][:-1]
            removals.append(f"{key}: dropped the last entry to fit the reading budget")

    # 3. Then the pair spans. A panel needs to name its side, not narrate it.
    if visible() > allowed:
        for key in ("left", "right"):
            value = str(payload.get(key) or "")
            if word_count(value) > 6:
                payload[key] = _headline_trim(value, 6)
                removals.append(f"{key}: shortened to the phrase it names")

    # 4. Then item text, at one shared limit so the list stays one list.
    if visible() > allowed:
        for key in ("items", "nodes", "children"):
            value = payload.get(key)
            if not isinstance(value, list):
                continue
            if any(word_count(str(v)) > 7 for v in value):
                payload[key] = [_headline_trim(str(v), 7) for v in value]
                removals.append(f"{key}: entries shortened to fit the reading budget")

    # 5. Last, the headline, cut at a clause boundary.
    if visible() > allowed and payload.get("headline"):
        head_budget = max(3, allowed - (visible() - word_count(str(payload["headline"]))))
        trimmed = _headline_trim(str(payload["headline"]), head_budget)
        if trimmed and trimmed != payload["headline"]:
            payload["headline"] = trimmed
            removals.append("headline cut at a clause boundary to fit the reading budget")

    share = (visible() / spoken) if spoken else 0.0
    return {
        "allowed_words": allowed,
        "speech_share": round(share, 3),
        "speech_share_target": share_max,
        "words_before": before,
        "words_after": visible(),
        "spoken_words": spoken,
        "removals": removals,
    }
