"""EventMath 2.0 extraction (skills/eventmath, skills/eventmath-extraction).

Everything is an event. An event is who + what + where + when + why + how,
composed of seven universal elements, located by a LENS x DIRECTION x QUANTIFIER
triple. This module turns one scene's text into that object.

It is pure pattern matching — no model, no lookup, no network — matching the
Second Brain's own extraction engine, so the same transcript always yields the
same event and the output is interoperable with the rest of the stack.

The gap contract is the part that matters most here. A 5W+H field the speaker
did not state is REPORTED as a gap and never filled: an invented actor or a
fabricated date is the same class of failure as a fabricated baseline on a bar
chart, and this compiler refuses both.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ..utils import normalize_whitespace, words
from .lexicon import Lexicon

_W_FIELDS = ("who", "what", "when", "where", "why", "how")

# Virtual locations resolve before geographic ones, or "Alberta" matches before
# "Zoom" in "the Alberta team met on Zoom".
_VIRTUAL_PLACES = re.compile(
    r"\b(Microsoft Teams|Google Meet|Zoom|Webex|Slack|Discord|YouTube|LinkedIn|online)\b",
    re.IGNORECASE,
)
_GEO_PLACES = re.compile(
    r"\b(Calgary|Edmonton|Toronto|Vancouver|Montreal|Ottawa|Alberta|Ontario|"
    r"British Columbia|Canada|the office|the room|home)\b",
    re.IGNORECASE,
)
_WHY = re.compile(r"\b(?:because|due to|caused by|so that|in order to)\s+([^.;]{3,80})", re.IGNORECASE)
_HOW = re.compile(r"\b(?:via|through|using|by)\s+((?:[a-z0-9][\w'-]*\s*){1,6})", re.IGNORECASE)
_WHEN = re.compile(
    r"\b((?:19|20)\d{2}"
    r"|at (?:the age of |age )?(?:forty|thirty|twenty|fifty|sixty)(?:[- ]\w+)?"
    r"|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*\d*"
    r"|(?:yesterday|today|tomorrow|tonight)"
    r"|every (?:year|month|week|day)"
    r"|(?:last|next|this) (?:year|month|week|quarter|decade))\b",
    re.IGNORECASE,
)


@dataclass
class Event:
    """One scene as an EventMath event object."""

    who: str | None = None
    what: str | None = None
    when: str | None = None
    where: str | None = None
    why: str | None = None
    how: str | None = None

    lens: str = "what"
    direction: str = "keep_same"
    quantifier: str = "one"

    elements: dict[str, list[str]] = field(default_factory=dict)
    category: str = "fact"
    signal: bool = True
    origin: str = "stated"
    gaps: list[str] = field(default_factory=list)
    actors: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "lens": self.lens,
            "direction": self.direction,
            "quantifier": self.quantifier,
            "category": self.category,
            "signal": self.signal,
            "origin": self.origin,
        }
        for name in _W_FIELDS:
            value = getattr(self, name)
            if value:
                out[name] = value
        if self.elements:
            out["elements"] = self.elements
        if self.gaps:
            out["gaps"] = self.gaps
        if self.actors:
            out["actors"] = self.actors
        return out


def _first_match(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns or []:
        found = re.search(pattern, text, flags=re.IGNORECASE)
        if found:
            return found.group(0)
    return None


def _pick(text: str, groups: dict[str, list[str]], order: list[str], default: str) -> str:
    for name in order:
        if _first_match(text, groups.get(name, []) or []):
            return name
    return default


def _extract_actors(text: str, vocab: dict[str, Any]) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    for kind, patterns in (vocab.get("actor_triggers") or {}).items():
        for pattern in patterns or []:
            for match in re.finditer(pattern, text):
                name = normalize_whitespace(match.group(match.lastindex or 0))
                if name and name.lower() not in seen and len(name.split()) <= 4:
                    seen.add(name.lower())
                    # The role is what the sentence shows them doing. Guessing
                    # beneficiary or payer from a name alone would be invention.
                    found.append({"name": name, "evidence": kind, "role": "user"})
    return found[:4]


def _elements_from_payload(payload: dict[str, Any], vocab: dict[str, Any], text: str = "") -> dict[str, list[str]]:
    """Which universal elements this scene actually carries.

    Read from the payload rather than from the words: an element is present when
    there is something to draw for it, which is the same test the obligation
    contract uses everywhere else.
    """
    present: dict[str, list[str]] = {}
    for name, spec in (vocab.get("elements") or {}).items():
        requires = spec.get("requires") or []
        if requires and not any(re.search(p, text, flags=re.IGNORECASE) for p in requires):
            continue
        filled: list[str] = []
        for key in spec.get("payload_keys", []) or []:
            value = payload.get(key)
            if isinstance(value, list) and value:
                for entry in value[:6]:
                    # Events are dicts; stringifying them put "{'event': ...}"
                    # into the element list and out through the API.
                    if isinstance(entry, dict):
                        text_value = entry.get("event") or entry.get("label") or ""
                    else:
                        text_value = str(entry)
                    if str(text_value).strip():
                        filled.append(str(text_value).strip())
            elif isinstance(value, str) and value.strip():
                filled.append(value.strip())
        if filled:
            present[name] = filled
    # A begin state with no end state is an incomplete transformation. Keeping
    # the half that was stated is honest; drawing a pair from it is not.
    for left, right in (vocab.get("element_pairs") or []):
        if left in present and right not in present:
            present.pop(left, None)
        elif right in present and left not in present:
            present.pop(right, None)
    return present


def _is_noise(text: str, vocab: dict[str, Any]) -> bool:
    spec = vocab.get("noise") or {}
    for pattern in spec.get("patterns", []) or []:
        if re.match(pattern, text.strip(), flags=re.IGNORECASE):
            return True
    tokens = words(text)
    if len(tokens) < int(spec.get("min_content_words", 3)):
        return True
    return False


def _quantifier(text: str, payload: dict[str, Any], vocab: dict[str, Any]) -> str:
    spec = vocab.get("quantifier") or {}
    # Cardinality is the deterministic anchor: four peers on screen is `many`
    # whatever the sentence says, and it keeps the quantifier and the topology
    # table from disagreeing about the same scene.
    count = 0
    for key in ("items", "nodes", "children", "series", "events", "points"):
        value = payload.get(key)
        if isinstance(value, list):
            count = len(value)
            break
    table = {int(k): str(v) for k, v in (spec.get("from_cardinality") or {}).items()}
    if count and table:
        for threshold in sorted(table, reverse=True):
            if count >= threshold:
                cardinal = table[threshold]
                break
        else:
            cardinal = spec.get("default", "one")
    else:
        cardinal = None

    lexical = _pick(text, spec.get("triggers") or {}, list(spec.get("values") or []), "")
    # `none` and `partial` are claims about scope that a count cannot overrule:
    # "not all customers" is partial even with four names on screen.
    if lexical in {"none", "partial"}:
        return lexical
    return cardinal or lexical or str(spec.get("default", "one"))


_FIRST_PERSON = re.compile(r"\b(?:I|I'm|I've|I'd|I'll|me|my|mine|we|we're|we've|our|us)\b", re.IGNORECASE)


def extract_event(
    text: str,
    payload: dict[str, Any],
    vocab: dict[str, Any],
    lex: Lexicon | None = None,
    speaker: str | None = None,
) -> Event:
    clean = normalize_whitespace(text)
    event = Event()
    if not clean:
        event.gaps = list(_W_FIELDS)
        event.signal = False
        return event

    # --- the triple ---------------------------------------------------------
    lens_spec = vocab.get("lens") or {}
    event.lens = _pick(clean, lens_spec.get("triggers") or {},
                       [n for n in (lens_spec.get("order") or []) if n != "what"],
                       str(lens_spec.get("default", "what")))
    direction_spec = vocab.get("direction") or {}
    event.direction = _pick(clean, direction_spec.get("triggers") or {},
                            list(direction_spec.get("values") or []),
                            str(direction_spec.get("default", "keep_same")))
    event.quantifier = _quantifier(clean, payload, vocab)

    # --- 5W+H ---------------------------------------------------------------
    actors = _extract_actors(clean, vocab)
    event.actors = actors
    if actors:
        event.who = actors[0]["name"]
    elif speaker and _FIRST_PERSON.search(clean):
        # First person resolves to the known speaker. That is stated context
        # from the project, not a filled gap — the transcript really is them.
        event.who = speaker
        event.actors = [{"name": speaker, "evidence": "first_person", "role": "user"}]
    event.what = str(payload.get("headline") or "").strip() or None

    when = _WHEN.search(clean)
    event.when = normalize_whitespace(when.group(1)) if when else None

    virtual = _VIRTUAL_PLACES.search(clean)
    geographic = _GEO_PLACES.search(clean)
    event.where = normalize_whitespace((virtual or geographic).group(1)) if (virtual or geographic) else None

    why = _WHY.search(clean)
    event.why = normalize_whitespace(why.group(1)) if why else None

    how = _HOW.search(clean)
    event.how = normalize_whitespace(how.group(1)) if how else None

    # --- elements, classification, gaps -------------------------------------
    event.elements = _elements_from_payload(payload, vocab, clean)
    category_spec = vocab.get("category") or {}
    event.category = _pick(clean, category_spec.get("triggers") or {},
                           list(category_spec.get("order") or []),
                           str(category_spec.get("default", "fact")))
    event.signal = not _is_noise(clean, vocab)
    event.origin = "stated"
    event.gaps = [name for name in _W_FIELDS if not getattr(event, name)]
    return event
