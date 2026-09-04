"""The resolution pipeline from SEMANTIC_MAPPING.md §14.

Precedence, strictly:

    1.  author tag                  (explicit override, always wins)
    2.  attached structured data    (defines what is measurable)
    3.  multiword expression        (idioms)
    4.  frame evocation             (roles -> visual slots)
    5.  image schema                (prepositions + verb class -> diagram family)
    6.  aspectual class             (Vendler -> motion operator)
    7.  primary metaphor licence    (spatial encoding permitted as literal)
    8.  concreteness                (icon vs schematic vs typography)
    9.  modality and evidentiality  (rendering weight, precision limits)
    10. information structure       (reveal order, which mark is hero)
    11. cross-modal bias            (<= 2 pt tiebreak only)
    12. kinetic typography          (congruence-safe default)

Note what is absent: any step where a single noun selects a template. The noun
never chooses the graphic. The relation does, and the relation lives in the
verb, the preposition, the frame and the aspect.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ..utils import normalize_whitespace, words
from .lexicon import Lexicon, load_lexicon

# Function words that cannot be a role filler on their own.
_SKIP = {
    "the", "a", "an", "and", "or", "but", "so", "of", "to", "in", "on", "at", "for",
    "from", "with", "by", "as", "that", "this", "it", "its", "is", "are", "was", "were",
    "be", "been", "i", "we", "you", "they", "he", "she", "my", "our", "their",
}

# Modals and auxiliaries carry a dominant NOUN part of speech in the
# concreteness norms ("can" the container, "will" the testament), so without
# this list "a framework that can evolve" resolves its head noun to "can" and
# licenses a photograph of a tin.
_NOT_A_HEAD = {
    "can", "will", "may", "might", "must", "could", "would", "should", "shall",
    "do", "does", "did", "done", "has", "have", "had", "being", "been", "am",
    "get", "got", "let", "make", "made", "put", "take", "took", "come", "came",
    "go", "went", "gone", "one", "two", "way", "thing", "things", "lot", "kind",
    "sort", "time", "times", "own", "just", "very", "really", "still", "even",
}

_CONTRAST = re.compile(r"\bnot\s+(?P<given>.+?)\s+but\s+(?P<focus>.+)", re.IGNORECASE)
_CLEFT = re.compile(
    r"\b(?:what|all)\s+(?:really\s+)?(?:matters|counts|changed|mattered)\s+(?:is|was)\s+(?P<focus>.+)",
    re.IGNORECASE,
)
_IT_CLEFT = re.compile(r"\bit(?:'s|s| is| was)\s+(?P<focus>.+?)\s+that\b", re.IGNORECASE)
_NUMBER = re.compile(r"\b\d[\d,.]*\s*(?:%|percent|per cent)?", re.IGNORECASE)
_HEDGED_NUMBER = re.compile(
    r"\b(?:roughly|about|around|approximately|nearly|almost|an estimated|over|under|more than|less than)\s+\d",
    re.IGNORECASE,
)


@dataclass
class SemanticAnalysis:
    """Everything the selector and renderer need, derived and auditable."""

    text: str = ""
    schema: str | None = None
    schema_label: str | None = None
    schema_template: str | None = None
    schema_needs_element: str | None = None
    schema_evidence: list[str] = field(default_factory=list)

    frame: str | None = None
    roles: dict[str, str] = field(default_factory=dict)
    unfilled_core_roles: list[str] = field(default_factory=list)
    obligations: list[str] = field(default_factory=list)
    requires_numeric: bool = False

    aspect: str = "state"
    motion_operator: str = "static"
    aspect_signals: list[str] = field(default_factory=list)

    modality: str = "asserted"
    modality_render: dict[str, Any] = field(default_factory=dict)
    label_precision: str = "exact"

    negation: dict[str, Any] | None = None

    head_noun: str | None = None
    concreteness_band: str = "unknown"
    concreteness_value: float | None = None
    depiction: str = "typography"

    metaphor_licences: list[str] = field(default_factory=list)
    cultural_metaphors: list[str] = field(default_factory=list)

    given: str | None = None
    focus: str | None = None
    reveal_order: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        out = {
            "schema": self.schema,
            "schema_template": self.schema_template,
            "schema_needs_element": self.schema_needs_element,
            "schema_evidence": self.schema_evidence,
            "frame": self.frame,
            "roles": self.roles,
            "unfilled_core_roles": self.unfilled_core_roles,
            "obligations": self.obligations,
            "requires_numeric": self.requires_numeric,
            "aspect": self.aspect,
            "motion_operator": self.motion_operator,
            "aspect_signals": self.aspect_signals,
            "modality": self.modality,
            "label_precision": self.label_precision,
            "negation": self.negation,
            "head_noun": self.head_noun,
            "concreteness_band": self.concreteness_band,
            "depiction": self.depiction,
            "metaphor_licences": self.metaphor_licences,
            "cultural_metaphors": self.cultural_metaphors,
            "focus": self.focus,
        }
        if self.concreteness_value is not None:
            out["concreteness_value"] = round(self.concreteness_value, 2)
        return {k: v for k, v in out.items() if v not in (None, [], {}, False)}


# --------------------------------------------------------------- §2 schema ---
def detect_schema(text: str, lex: Lexicon) -> tuple[Any | None, list[str]]:
    """First schema in precedence order whose trigger fires.

    Precedence is by trigger specificity, not frequency: blockage before force,
    because "prevented" is also a causal verb but the blocked reading is the
    stronger claim.
    """
    for rule in lex.schemas:
        evidence = [p.pattern for p in rule.patterns if p.search(text)]
        if evidence:
            return rule, evidence
    return None, []


# ---------------------------------------------------------------- §3 frame ---
def _span_role(text: str, trigger: re.Match[str], side: str) -> str:
    raw = text[: trigger.start()] if side == "before" else text[trigger.end():]
    raw = normalize_whitespace(raw).strip(" ,;:.—–-")
    tokens = raw.split()
    while tokens and tokens[0].lower().strip(",.;:") in _SKIP:
        tokens.pop(0)
    while tokens and tokens[-1].lower().strip(",.;:") in _SKIP:
        tokens.pop()
    span = " ".join(tokens[:10]).strip(" ,;:.—–-")
    return span


def evoke_frame(text: str, lex: Lexicon) -> tuple[Any | None, dict[str, str], list[str]]:
    """Find the evoking verb, then fill only the roles the text actually fills."""
    lowered = text.lower()
    best: tuple[Any, re.Match[str]] | None = None
    for token in words(lowered):
        rule = lex.frame_index.get(token)
        if rule is None:
            continue
        # An ambiguous lemma only evokes its frame inside the construction that
        # makes it that verb: "leads TO", not "potential leads".
        guard = lex.frame_constraints.get(token)
        if guard is not None and not guard.search(text):
            continue
        match = re.search(rf"\b{re.escape(token)}\b", text, flags=re.IGNORECASE)
        if match and (best is None or match.start() < best[1].start()):
            best = (rule, match)
    if best is None:
        return None, {}, []

    rule, trigger = best
    roles: dict[str, str] = {}
    slots = {name: spec.get("slot") for name, spec in rule.roles.items()}

    left = _span_role(text, trigger, "before")
    right = _span_role(text, trigger, "after")
    used: set[str] = set()

    def claim(name: str, span: str) -> None:
        # A span fills at most one role. Letting "Disbelief" land in both
        # `cause` and `actor` doubles a mark the sentence licenses once.
        if span and span not in used:
            roles[name] = span
            used.add(span)

    for name, spec in sorted(rule.roles.items(), key=lambda kv: not kv[1].get("core")):
        slot = spec.get("slot")
        if slot in {"left", "barrier", "centre", "boundary", "entity_label"}:
            claim(name, left)
        elif slot in {"right", "blocked", "parts", "outputs", "headline"}:
            claim(name, right)

    # A quantity is only a filled role when a number is actually present.
    number = _NUMBER.search(text)
    if number:
        figure = number.group(0).strip()
        for name, spec in rule.roles.items():
            if spec.get("slot") == "hero_mark":
                roles[name] = figure
                used.add(figure)
        # A role whose span is really just the figure with a hedge glued to it
        # ("estimated 96") is not an entity label; drop it rather than print it.
        digits = re.sub(r"[^\d]", "", figure)
        for name in [n for n, v in roles.items() if rule.roles.get(n, {}).get("slot") != "hero_mark"]:
            span_digits = re.sub(r"[^\d]", "", roles[name])
            if digits and span_digits == digits and len(roles[name]) <= len(figure) + 12:
                roles.pop(name, None)

    time_match = re.search(
        r"\b(?:after|before|since|during|in|by|at)\s+(?:the\s+)?"
        r"((?:19|20)\d{2}"
        r"|age\s+[\w-]+"
        r"|(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"|(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
        r"|(?:campaign|launch|diagnosis|pandemic|war|merger|election|move|change|start|beginning|end)\b"
        r"|(?:last|next|this|that)\s+(?:year|month|week|day|quarter|decade))",
        text, flags=re.IGNORECASE,
    )
    if time_match:
        for name, spec in rule.roles.items():
            if spec.get("slot") == "time_label":
                roles.setdefault(name, normalize_whitespace(time_match.group(0)))
                break

    # The obligation contract: a core role the text did not fill stays unfilled,
    # and the visual must not invent a mark for it.
    unfilled = [
        name for name, spec in rule.roles.items()
        if spec.get("core") and name not in roles
    ]
    obligations = sorted({slots[name] for name in roles if slots.get(name)})
    return rule, roles, unfilled if not obligations else unfilled


# --------------------------------------------------------------- §5 aspect ---
def classify_aspect(text: str, lex: Lexicon) -> tuple[str, str, list[str]]:
    lowered = text.lower()
    token_set = set(words(lowered))
    signals = [
        name for name, spec in lex.aspect_signals.items()
        if any(re.search(p, text, flags=re.IGNORECASE) for p in spec.get("markers", []) or [])
    ]

    # Achievements are punctual and win over everything: "was diagnosed" is an
    # instantaneous state change even inside a long sentence.
    order = ["achievement", "accomplishment", "activity", "state"]
    for class_id in order:
        spec = lex.aspect_classes.get(class_id) or {}
        verbs = {str(v).lower() for v in spec.get("verbs", []) or []}
        markers = spec.get("markers", []) or []
        if token_set & verbs or any(re.search(p, text, flags=re.IGNORECASE) for p in markers):
            return class_id, str(spec.get("motion_operator", "static")), signals

    fallback = lex.aspect_classes.get("state") or {}
    return "state", str(fallback.get("motion_operator", "static")), signals


# ------------------------------------------------------------- §7 modality ---
def detect_modality(text: str, lex: Lexicon) -> tuple[str, dict[str, Any]]:
    # Most specific first: an approximated number outranks a bare future.
    order = ["attributed", "approximate", "forecast", "possible", "contingent", "asserted"]
    for level in order:
        spec = lex.modality_levels.get(level) or {}
        markers = spec.get("markers", []) or []
        if markers and any(re.search(p, text, flags=re.IGNORECASE) for p in markers):
            return level, dict(spec.get("render", {}) or {})
    asserted = lex.modality_levels.get("asserted") or {}
    return "asserted", dict(asserted.get("render", {}) or {})


# ------------------------------------------------------------- §8 negation ---
def detect_negation(text: str, lex: Lexicon) -> dict[str, Any] | None:
    markers = lex.negation.get("markers", {}) or {}
    hit = None
    for kind, patterns in markers.items():
        for pattern in patterns or []:
            if re.search(pattern, text, flags=re.IGNORECASE):
                hit = kind
                break
        if hit:
            break
    if not hit:
        return None
    result: dict[str, Any] = {
        "kind": hit,
        "show_positive_first": bool((lex.negation.get("render") or {}).get("show_positive_first", True)),
        "element": (lex.negation.get("render") or {}).get("element", "strike_through"),
        "target": "predicate",
        "survives": "none",
    }
    # Scope matters: "not [all agreed]" leaves a partial group standing, while
    # "[all] did not agree" negates the group. Different truth conditions.
    for rule in lex.negation.get("scope", []) or []:
        if re.search(str(rule.get("pattern", "")), text, flags=re.IGNORECASE):
            result["target"] = rule.get("target", "predicate")
            result["survives"] = rule.get("survives", "none")
            result["scope_rule"] = rule.get("id")
            break
    return result


# -------------------------------------------------------- §4 depiction gate ---
def depiction_gate(head_noun: str | None, schema_id: str | None, lex: Lexicon) -> tuple[str, str, float | None]:
    """Decide icon vs schematic vs typography.

    Schema concreteness and referent concreteness are separate tests. A causal
    arrow is licensed by a concrete FORCE schema even when both entities are
    abstract; an icon of "disbelief" never is.
    """
    band, value = lex.concreteness_of(head_noun or "")
    if band == "concrete":
        return "photograph", band, value
    if band == "semi":
        return "icon", band, value
    if band == "abstract":
        return ("schematic" if schema_id else "typography"), band, value
    # Unknown: abstain. Never license a depiction on a word we have no rating
    # for; fall back to the relation if one was detected.
    return ("schematic" if schema_id else "typography"), band, value


def head_noun_of(text: str, lex: Lexicon) -> str | None:
    """The rightmost rated content word. Crude, but deterministic and auditable.

    Preferring the rightmost is the English default: in a noun phrase the head
    sits at the end ("accessibility-first web design" -> design).
    """
    candidates = [
        w.lower() for w in words(text)
        if w.lower() not in _SKIP and w.lower() not in _NOT_A_HEAD and len(w) > 2
    ]
    for token in reversed(candidates):
        band, _ = lex.concreteness_of(token)
        if band != "unknown":
            return token
    return candidates[-1] if candidates else None


# --------------------------------------------- §6 information structure ------
def information_structure(text: str) -> tuple[str | None, str | None]:
    """Return (given, focus).

    Prosodic focus is the strongest cue, but from an SRT there is no F0 track,
    so this approximates it with the constructions that grammaticalise focus:
    contrast, clefts, and post-verbal position.
    """
    match = _CONTRAST.search(text)
    if match:
        return normalize_whitespace(match.group("given")), normalize_whitespace(match.group("focus")).strip(" .")
    for pattern in (_CLEFT, _IT_CLEFT):
        match = pattern.search(text)
        if match:
            return None, normalize_whitespace(match.group("focus")).strip(" .")
    # Default: the last substantial phrase carries the new information.
    tail = re.split(r"[,;:]", normalize_whitespace(text))[-1].strip(" .")
    return None, tail or None


# ------------------------------------------------------------ §1 metaphor ----
def metaphor_licences(text: str, lex: Lexicon) -> tuple[list[str], list[str]]:
    licensed: list[str] = []
    for name, spec in (lex.metaphors.get("primary", {}) or {}).items():
        if any(re.search(p, text, flags=re.IGNORECASE) for p in spec.get("evidence", []) or []):
            licensed.extend(spec.get("licenses", []) or [])
    cultural = [
        str(entry.get("id"))
        for entry in (lex.metaphors.get("cultural", []) or [])
        if any(re.search(p, text, flags=re.IGNORECASE) for p in entry.get("evidence", []) or [])
    ]
    return sorted(set(licensed)), cultural


# ---------------------------------------------------------------- pipeline ---
def analyze(text: str, lex: Lexicon | None = None, grammar_dir: str | None = None) -> SemanticAnalysis:
    lex = lex or load_lexicon(grammar_dir)
    clean = normalize_whitespace(text)
    result = SemanticAnalysis(text=clean)
    if not clean:
        return result

    schema_rule, evidence = detect_schema(clean, lex)
    if schema_rule is not None:
        result.schema = schema_rule.id
        result.schema_label = schema_rule.label
        result.schema_template = schema_rule.template
        result.schema_needs_element = schema_rule.needs_element
        result.schema_evidence = evidence

    frame_rule, roles, unfilled = evoke_frame(clean, lex)
    if frame_rule is not None:
        result.frame = frame_rule.id
        result.roles = roles
        result.unfilled_core_roles = unfilled
        result.requires_numeric = frame_rule.requires_numeric
        result.obligations = sorted({
            str(frame_rule.roles[name].get("slot"))
            for name in roles
            if frame_rule.roles.get(name, {}).get("slot")
        })
        # A frame's own schema wins over a bare trigger match: the frame carries
        # role structure, the schema only carries a shape.
        if frame_rule.schema and not result.schema:
            result.schema = frame_rule.schema

    result.aspect, result.motion_operator, result.aspect_signals = classify_aspect(clean, lex)
    result.modality, result.modality_render = detect_modality(clean, lex)
    result.label_precision = str(result.modality_render.get("label", "exact"))
    # A hedged number can never render at full precision, whatever the modality
    # marker resolution said.
    if _HEDGED_NUMBER.search(clean):
        result.label_precision = "rounded"

    result.negation = detect_negation(clean, lex)
    result.head_noun = head_noun_of(clean, lex)
    result.depiction, result.concreteness_band, result.concreteness_value = depiction_gate(
        result.head_noun, result.schema, lex
    )
    result.metaphor_licences, result.cultural_metaphors = metaphor_licences(clean, lex)
    result.given, result.focus = information_structure(clean)

    # Reveal order mirrors the sentence's own information flow, so the eye and
    # the ear reach the point together.
    order: list[str] = []
    if result.given:
        order.append("given")
    order.extend(slot for slot in result.obligations if slot not in {"hero_mark"})
    if "hero_mark" in result.obligations:
        order.append("hero_mark")
    if result.focus:
        order.append("focus")
    result.reveal_order = order
    return result
