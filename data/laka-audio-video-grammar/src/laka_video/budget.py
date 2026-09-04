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
import re
from typing import Any

from .ordering import RENDERED_FIELDS, visible_words_for
from .text_rules import _trim_trailing_function_words
from .utils import word_count


# A clause opening with one of these is SUBORDINATE: it cannot stand alone, so
# cutting after it strands the subordinator. "When a rule helps, we should
# understand why" cut at the comma leaves "When a rule helps", which is a
# question the frame never answers.
_SUBORDINATORS = {
    "when", "whenever", "if", "unless", "because", "since", "while", "whereas",
    "although", "though", "even", "after", "before", "until", "till", "as",
    "once", "provided", "whether", "wherever", "so", "lest",
}


def _stands_alone(text: str) -> bool:
    tokens = text.split()
    if not tokens:
        return False
    return re.sub(r"[^\w]", "", tokens[0].lower()) not in _SUBORDINATORS


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
        if found and word_count(candidate) >= 3 and _stands_alone(candidate):
            return candidate

    # No clause boundary inside the window. Without a parser there is no way to
    # tell "You might know" from a finished phrase, so nothing is cut. The
    # headline arrived from _headline_span already cut at a boundary; cutting it
    # again on word count alone is how "I'm a cognitive architect" became
    # "I'm a cognitive".
    return source


def _norm(value: Any) -> str:
    return " ".join("".join(c for c in str(value).lower() if c.isalnum() or c == " ").split())


def _echoes(a: Any, b: Any) -> bool:
    left, right = _norm(a), _norm(b)
    if not left or not right:
        return False
    if left == right:
        return True
    short, long = (left, right) if len(left) <= len(right) else (right, left)
    return len(short.split()) >= 4 and short in long


def dedupe_payload(payload: dict[str, Any]) -> list[str]:
    """Collapse alternate encodings of the same sentence.

    The text pass extracts a headline, a hub, a node list and an item list from
    ONE sentence, opportunistically, so a payload can hold four copies of the
    same words. The renderer already suppresses the duplicates at draw time,
    but every measurement upstream counted them: a 16-word line measured as 42
    words on screen and no amount of trimming could converge, because the words
    were never really there.
    """
    removed: list[str] = []

    # An item list identical to the node list is one list stored twice.
    if isinstance(payload.get("items"), list) and isinstance(payload.get("nodes"), list):
        if [_norm(v) for v in payload["items"]] == [_norm(v) for v in payload["nodes"]]:
            payload.pop("items")
            removed.append("items: identical to nodes")

    # Events whose text is the item list are the same list with a time column.
    events = payload.get("events")
    if isinstance(events, list) and isinstance(payload.get("items"), list):
        texts = [_norm(e.get("event")) if isinstance(e, dict) else _norm(e) for e in events]
        items = [_norm(v) for v in payload["items"]]
        if texts == items or all(any(_echoes(i, t) for t in texts) for i in items):
            payload.pop("items")
            removed.append("items: already carried by events")

    # A time column that reads the same on every row is not an axis, it is a
    # word repeated down the side of the frame. "When / When / When" carries no
    # information and costs a fixation each.
    if isinstance(events, list) and len(events) > 1:
        times = [_norm(e.get("time")) if isinstance(e, dict) else "" for e in events]
        looks_temporal = any(
            t and (t[:1].isdigit() or t.split()[0] in {
                "january", "february", "march", "april", "may", "june", "july",
                "august", "september", "october", "november", "december",
                "monday", "tuesday", "wednesday", "thursday", "friday",
                "saturday", "sunday", "today", "yesterday", "tomorrow",
            })
            for t in times
        )
        if not looks_temporal or len(set(times)) == 1:
            for event in events:
                if isinstance(event, dict):
                    event.pop("time", None)
            removed.append("events: time column carried no information")

    # A hub that restates the headline is not a second mark.
    for key in ("center", "parent"):
        if payload.get(key) and _echoes(payload[key], payload.get("headline")):
            payload.pop(key)
            removed.append(f"{key}: restates the headline")

    # A node or item that restates the hub or the headline is not a peer.
    for key in ("nodes", "items", "children"):
        value = payload.get(key)
        if not isinstance(value, list):
            continue
        against = [payload.get("center"), payload.get("parent"), payload.get("headline")]
        kept = [v for v in value if not any(_echoes(v, a) for a in against if a)]
        if len(kept) != len(value) and len(kept) >= 1:
            payload[key] = kept
            removed.append(f"{key}: dropped entries restating the headline or hub")
        elif not kept:
            # Everything echoed: the list was never additional content.
            payload.pop(key)
            removed.append(f"{key}: entirely restated the headline")
    return removed


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
        """The worst case across every template this payload could reach.

        The budget runs before selection, so it cannot know which template wins
        and has to bound the heaviest outcome. An earlier version sampled only
        four templates and therefore never measured `nodes`, `children`,
        `events` or `series` at all — scenes that became a network or a timeline
        were handed 42 and 31 words on screen with no trimming applied.
        """
        return max(visible_words_for(template, payload) for template in RENDERED_FIELDS)

    # Collapse duplicate encodings before measuring anything: trimming a list
    # that is just the headline stored again removes content that was never on
    # screen and leaves the real overage untouched.
    removals.extend(dedupe_payload(payload))

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

    # 4a. Event text, at the same shared limit as any other list.
    if visible() > allowed and isinstance(payload.get("events"), list):
        if any(word_count(str(e.get("event", ""))) > 7 for e in payload["events"] if isinstance(e, dict)):
            for event in payload["events"]:
                if isinstance(event, dict) and event.get("event"):
                    event["event"] = _headline_trim(str(event["event"]), 7)
            removed_before = len(removals)
            removals.append("events: entries shortened to fit the reading budget")

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
