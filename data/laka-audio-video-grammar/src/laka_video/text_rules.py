from __future__ import annotations

import copy
import re
from typing import Any

from .utils import normalize_whitespace, word_count, words


_NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80,
    "ninety": 90, "hundred": 100,
}

_CONNECTOR_TRIM = re.compile(
    r"^(?:today|so|but|and|then|through|that means|this means|in other words|for example|"
    r"instead|before that|after that|the question is|the question isn[’']t just)\b[,:]?\s*",
    flags=re.IGNORECASE,
)


def _clean_fragment(text: str) -> str:
    value = normalize_whitespace(text)
    value = _CONNECTOR_TRIM.sub("", value)
    value = value.strip(" ,;:.—–-")
    if value:
        value = value[0].upper() + value[1:]
    return value


def _list_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_clean_fragment(str(v)) for v in value if _clean_fragment(str(v))]
    text = str(value)
    pieces = re.split(r"\s*\|\s*", text)
    return [_clean_fragment(p) for p in pieces if _clean_fragment(p)]


def _parse_number_word(token: str) -> int | None:
    parts = re.split(r"[-\s]+", token.lower())
    if not parts or any(p not in _NUMBER_WORDS for p in parts):
        return None
    total = 0
    current = 0
    for part in parts:
        n = _NUMBER_WORDS[part]
        if n == 100:
            current = max(1, current) * 100
        else:
            current += n
    total += current
    return total


def _number_from_text(text: str) -> tuple[str | None, str | None]:
    numeric = re.search(r"(?<!\w)(\$?\d+(?:[.,]\d+)?%?)(?!\w)", text)
    if numeric:
        token = numeric.group(1)
        unit = None
        if token.startswith("$"):
            unit = "currency"
        elif token.endswith("%"):
            unit = "percent"
        return token, unit
    number_pattern = "|".join(sorted(_NUMBER_WORDS, key=len, reverse=True))
    match = re.search(rf"\b((?:{number_pattern})(?:[- ](?:{number_pattern}))?)\b", text, flags=re.IGNORECASE)
    if match:
        parsed = _parse_number_word(match.group(1))
        if parsed is not None:
            return str(parsed), None
    return None, None


def _sentence_parts(text: str) -> list[str]:
    return [
        _clean_fragment(p)
        for p in re.split(r"(?<=[.!?])\s+|\s*[;—–]\s*", text)
        if _clean_fragment(p)
    ]


def _extract_items(text: str, maximum: int = 8) -> list[str]:
    source = text
    marker = re.search(
        r"\b(?:including|such as|things like|covering|for example|start(?:s|ed|ing)? with)\b\s*:?[ ]*(.+)",
        text,
        flags=re.IGNORECASE,
    )
    if marker:
        source = marker.group(1)
    elif ":" in text:
        source = text.split(":", 1)[1]

    # Protect common paired phrases from being split too aggressively.
    pieces = re.split(r"\s*[,;]\s*|\s+\band\b\s+|\s+\bor\b\s+", source, flags=re.IGNORECASE)
    cleaned = []
    for p in pieces:
        p = re.sub(r"^(?:first|second|third|fourth|finally|next|then)\b[,:]?\s*", "", p, flags=re.IGNORECASE)
        p = _clean_fragment(p)
        if 1 <= word_count(p) <= 14 and p not in cleaned:
            cleaned.append(p)
    if len(cleaned) < 2:
        sentences = _sentence_parts(text)
        if 2 <= len(sentences) <= maximum:
            cleaned = sentences
    return cleaned[:maximum]


def _extract_sequence_items(text: str, maximum: int = 8) -> list[str]:
    marker_re = re.compile(
        r"(?:^|(?<=[.!?])\s+)(?:first|second|third|fourth|fifth|next|then|finally)\b[,:-]?\s*",
        flags=re.IGNORECASE,
    )
    matches = list(marker_re.finditer(text))
    if len(matches) >= 2:
        items: list[str] = []
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            item = _clean_fragment(text[match.end():end])
            if item and item not in items:
                items.append(item)
        if len(items) >= 2:
            return items[:maximum]
    return _extract_items(text, maximum)


def _split_at_connector(text: str, patterns: list[tuple[str, str]]) -> tuple[str | None, str | None, str | None]:
    for name, pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        groups = match.groupdict()
        left = _clean_fragment(groups.get("left", ""))
        right = _clean_fragment(groups.get("right", ""))
        if left and right:
            return left, right, name
    return None, None, None


def _extract_pair(text: str, relation: str) -> tuple[str | None, str | None, str | None]:
    if relation == "transformation":
        return _split_at_connector(text, [
            ("from_to", r"\bfrom\s+(?P<left>.+?)\s+to\s+(?P<right>.+?)(?:[.!?]|$)"),
            ("turn_into", r"\bturn(?:s|ed|ing)?\s+(?P<left>.+?)\s+into\s+(?P<right>.+?)(?:[.!?]|$)"),
            ("become", r"(?P<left>.+?)\s+become(?:s|d|ing)?\s+(?P<right>.+?)(?:[.!?]|$)"),
        ])
    if relation in {"contrast", "comparison"}:
        return _split_at_connector(text, [
            ("instead_of", r"\binstead of\s+(?P<left>.+?)(?:,|\s+I\s+|\s+we\s+|\s+it\s+)(?P<right>.+?)(?:[.!?]|$)"),
            ("not_but", r"\bnot\s+(?P<left>.+?)\s+but\s+(?P<right>.+?)(?:[.!?]|$)"),
            ("but", r"(?P<left>.+?)\s+but\s+(?P<right>.+?)(?:[.!?]|$)"),
            ("however", r"(?P<left>.+?)(?:[.;,])?\s+however[,]?\s+(?P<right>.+?)(?:[.!?]|$)"),
            ("rather_than", r"\brather than\s+(?P<left>.+?)(?:,|\s+we\s+|\s+I\s+)(?P<right>.+?)(?:[.!?]|$)"),
            ("while", r"(?P<left>.+?)\s+while\s+(?P<right>.+?)(?:[.!?]|$)"),
            ("and_feel", r"(?P<left>.+?\blook\b.+?)\s+and\s+(?P<right>feel\b.+?)(?:[.!?]|$)"),
            ("versus", r"(?P<left>.+?)\s+(?:versus|vs\.?)\s+(?P<right>.+?)(?:[.!?]|$)"),
        ])
    if relation == "cause_effect":
        direct = _split_at_connector(text, [
            ("leads_to", r"(?P<left>.+?)\s+leads? to\s+(?P<right>.+?)(?:[.!?]|$)"),
            ("results_in", r"(?P<left>.+?)\s+results? in\s+(?P<right>.+?)(?:[.!?]|$)"),
            ("causes", r"(?P<left>.+?)\s+causes?\s+(?P<right>.+?)(?:[.!?]|$)"),
            ("creates", r"(?P<left>.+?)\s+creates?\s+(?P<right>.+?)(?:[.!?]|$)"),
            ("therefore", r"(?P<left>.+?)[,;.]?\s+therefore[,]?\s+(?P<right>.+?)(?:[.!?]|$)"),
        ])
        if direct[0]:
            return direct
        because = re.search(r"(?P<right>.+?)\s+because\s+(?P<left>.+?)(?:[.!?]|$)", text, flags=re.IGNORECASE)
        if because:
            return _clean_fragment(because.group("left")), _clean_fragment(because.group("right")), "because"
    if relation == "problem_solution":
        direct = _split_at_connector(text, [
            ("take_problem_build", r"(?:take|break)\s+(?P<left>.+?problem.*?)\s+(?:apart|down).+?(?:choose|build|create)\s+(?P<right>.+?)(?:[.!?]|$)"),
            ("problem_into_build", r"(?P<left>.+?problem.+?)\s+(?:into|toward)\s+(?P<right>.+?)(?:[.!?]|$)"),
        ])
        if direct[0]:
            return direct
        sentences = _sentence_parts(text)
        problem_words = re.compile(r"\b(problem|challenge|issue|obstacle|pain|stale|left behind|outside)\b", re.I)
        response_words = re.compile(r"\b(solve|solution|build|framework|approach|help|work differently|useful|tackles?)\b", re.I)
        left = next((s for s in sentences if problem_words.search(s)), None)
        right = next((s for s in sentences if response_words.search(s) and s != left), None)
        if left and right:
            return left, right, "problem_response_sentences"
        return _split_at_connector(text, [
            ("problem_colon", r"(?P<left>.+?\bproblem\b)\s*:\s*(?P<right>.+?)(?:[.!?]|$)"),
            ("tackles", r"(?P<right>.+?\btackles?\b)\s+(?P<left>.+?\bproblem\b.+?)(?:[.!?]|$)"),
        ])
    return None, None, None


def _extract_definition(text: str) -> tuple[str | None, str | None]:
    patterns = [
        r"(?P<term>.+?)\s+(?:means?|refers? to|is defined as)\s+(?P<definition>.+?)(?:[.!?]|$)",
        r"(?P<term>.+?)\s+is an?\s+(?P<definition>.+?)(?:[.!?]|$)",
        r"\bthat means\s+(?P<definition>.+?)(?:[.!?]|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            term = _clean_fragment(match.groupdict().get("term") or "This")
            definition = _clean_fragment(match.groupdict().get("definition") or "")
            if term and definition:
                return term, definition
    return None, None


def _headline(text: str, stopwords: set[str], relation: str, payload: dict[str, Any]) -> str:
    if relation in {"transformation", "contrast", "comparison", "cause_effect", "problem_solution"}:
        left, right = payload.get("left"), payload.get("right")
        if left and right and word_count(left) <= 7 and word_count(right) <= 7:
            return f"{left} → {right}"
    if relation == "definition" and payload.get("term"):
        return str(payload["term"])
    if relation == "quantity" and payload.get("number"):
        return str(payload.get("label") or payload["number"])
    if relation == "question":
        question = next((p for p in _sentence_parts(text) if p.endswith("?")), None)
        if question:
            return question

    if relation in {"list", "sequence", "hierarchy", "network", "cycle"} and ":" in text:
        lead = _clean_fragment(text.split(":", 1)[0])
        if lead:
            return " ".join(lead.split()[:7])
    if relation == "cta":
        lead = _clean_fragment(re.split(r"[,;:—–]", text, maxsplit=1)[0])
        if lead:
            return " ".join(lead.split()[:7])

    first = _sentence_parts(text)[0] if _sentence_parts(text) else _clean_fragment(text)
    first = _CONNECTOR_TRIM.sub("", first).strip()
    if word_count(first) <= 7:
        return first
    tokens = first.split()
    # Start at the first content-bearing token, then retain an exact source span.
    start = 0
    for i, token in enumerate(tokens[:5]):
        normalized = re.sub(r"[^\w'-]", "", token.lower())
        if normalized and normalized not in stopwords:
            start = i
            break
    return _clean_fragment(" ".join(tokens[start:start + 7]).rstrip(" ,;:"))


class TextRuleEngine:
    def __init__(self, lexicon: dict[str, Any]):
        self.lexicon = lexicon
        self.stopwords = set(lexicon.get("stopwords", []))
        self.patterns: dict[str, list[re.Pattern[str]]] = {}
        for relation, spec in lexicon.get("relations", {}).items():
            self.patterns[relation] = [re.compile(p, flags=re.IGNORECASE | re.DOTALL) for p in spec.get("patterns", [])]

    def classify(self, text: str, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        overrides = overrides or {}
        scores: dict[str, float] = {}
        evidence: dict[str, list[str]] = {}
        for relation, spec in self.lexicon.get("relations", {}).items():
            base = float(spec.get("base_weight", 1.0))
            relation_score = 0.0
            relation_evidence: list[str] = []
            for pattern in self.patterns.get(relation, []):
                matches = list(pattern.finditer(text))
                if matches:
                    relation_score += base + max(0, len(matches) - 1) * base * 0.35
                    relation_evidence.append(pattern.pattern)
            if relation_score > 0:
                scores[relation] = relation_score
                evidence[relation] = relation_evidence

        # A single temporal word is context, not enough evidence for a timeline infographic.
        temporal_hits = re.findall(r"\b(?:before|after|today|later|when|at\s+(?:age\s+)?[\w-]+|in\s+(?:19|20)\d{2})\b", text, flags=re.IGNORECASE)
        if "timeline" in scores and len(temporal_hits) < 2 and len(_sentence_parts(text)) < 2:
            scores["timeline"] = min(scores["timeline"], 0.6)
            evidence.setdefault("timeline", []).append("single_temporal_context_reduced")

        if text.rstrip().endswith("?"):
            scores["question"] = scores.get("question", 0.0) + 4.0
            evidence.setdefault("question", []).append("question_mark")
        if ":" in text:
            scores["list"] = scores.get("list", 0.0) + 1.5
            evidence.setdefault("list", []).append("colon")
        if text.count(",") >= 2 and re.search(r"\b(?:and|or)\b", text, flags=re.IGNORECASE):
            scores["list"] = scores.get("list", 0.0) + 3.0
            evidence.setdefault("list", []).append("comma_series")
        if _number_from_text(text)[0] is not None:
            scores["quantity"] = scores.get("quantity", 0.0) + 3.0
            evidence.setdefault("quantity", []).append("number_token")
        if not scores:
            scores["emphasis"] = 1.0
            evidence["emphasis"] = ["fallback"]
        elif "emphasis" not in scores:
            scores["emphasis"] = 0.8

        priority = {
            "cta": 100, "warning": 98, "question": 96, "transformation": 92,
            "cause_effect": 90, "problem_solution": 88, "comparison": 86, "contrast": 84,
            "definition": 82, "conditional": 80, "sequence": 78, "identity": 76, "timeline": 74,
            "hierarchy": 72, "network": 70, "cycle": 68, "quantity": 66,
            "list": 60, "emphasis": 1,
        }
        automatic = max(scores, key=lambda k: (scores[k], priority.get(k, 0), k))
        selected = str(overrides.get("relation") or automatic)
        if selected not in scores:
            scores[selected] = max(scores.values()) + 0.1
            evidence[selected] = ["author_override"]

        speech_act = "statement"
        for act, patterns in self.lexicon.get("speech_acts", {}).items():
            if any(re.search(p, text, flags=re.IGNORECASE) for p in patterns):
                speech_act = act
                break
        sensitive = any(re.search(p, text, flags=re.IGNORECASE) for p in self.lexicon.get("sensitive_terms", []))

        payload = self.extract_payload(text, selected, overrides)
        # Secondary relations can contribute literal payload fields without changing the primary relation.
        for auxiliary in ("quantity", "cta", "list", "sequence", "timeline"):
            if auxiliary in scores and auxiliary != selected:
                auxiliary_payload = self.extract_payload(text, auxiliary, {})
                for key, value in auxiliary_payload.items():
                    payload.setdefault(key, value)
        payload.setdefault("headline", _headline(text, self.stopwords, selected, payload))
        payload.setdefault("supporting", normalize_whitespace(text))
        return {
            "automatic_relation": automatic,
            "primary_relation": selected,
            "relation_scores": {k: round(v, 4) for k, v in sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))},
            "evidence": evidence,
            "speech_act": speech_act,
            "sensitive": sensitive,
            "payload": payload,
        }

    def extract_payload(self, text: str, relation: str, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        overrides = copy.deepcopy(overrides or {})
        payload: dict[str, Any] = {}

        if relation in {"list", "sequence", "cycle"}:
            items = _extract_sequence_items(text) if relation == "sequence" else _extract_items(text)
            if items:
                payload["items"] = items
                if relation == "sequence":
                    payload["ordered"] = True
                if relation == "cycle":
                    payload["closed"] = True

        if relation in {"transformation", "contrast", "comparison", "cause_effect", "problem_solution"}:
            left, right, extraction = _extract_pair(text, relation)
            if left and right:
                payload.update({"left": left, "right": right, "pair_extraction": extraction})

        if relation == "definition":
            term, definition = _extract_definition(text)
            if term and definition:
                payload.update({"term": term, "definition": definition})

        if relation == "timeline":
            items = _sentence_parts(text)
            events = []
            for item in items[:6]:
                marker = re.search(
                    r"\b(before|after|today|later|when|at\s+[\w-]+|in\s+(?:19|20)\d{2})\b",
                    item,
                    flags=re.IGNORECASE,
                )
                events.append({"time": _clean_fragment(marker.group(1)) if marker else "", "event": item})
            if len(events) >= 2 and any(e.get("time") for e in events):
                payload["events"] = events
                payload["items"] = [e["event"] for e in events]

        if relation == "conditional":
            pairs = []
            for sentence in _sentence_parts(text):
                match = re.search(r"^(?:if|when|unless)\s+(?P<left>.+?),\s+(?P<right>.+)$", sentence, flags=re.IGNORECASE)
                if match:
                    left = _clean_fragment(match.group("left"))
                    right = _clean_fragment(match.group("right"))
                    if left and right:
                        pairs.append({"condition": left, "response": right})
            if len(pairs) == 1:
                payload.update({"left": pairs[0]["condition"], "right": pairs[0]["response"]})
            elif len(pairs) >= 2:
                payload["items"] = [f"{pair['condition']} → {pair['response']}" for pair in pairs[:4]]

        if relation == "hierarchy":
            items = _extract_items(text)
            first_clause = _sentence_parts(text)[0] if _sentence_parts(text) else text
            parent = _clean_fragment(first_clause.split(":", 1)[0])
            if parent and len(items) >= 2:
                payload.update({"parent": parent, "children": items})

        if relation == "network":
            items = _extract_items(text)
            candidates = [w for w in words(text) if w.lower() not in self.stopwords and len(w) > 3]
            center = _clean_fragment(" ".join(candidates[:3])) if candidates else _clean_fragment(text)
            if len(items) >= 2:
                payload.update({"center": center, "nodes": items})

        if relation == "quantity":
            number, unit = _number_from_text(text)
            if number:
                # Remove the literal numeric expression, including written numbers such as
                # “forty-one”. This preserves source wording without pretending to paraphrase.
                label = re.sub(re.escape(number), "", text, count=1, flags=re.IGNORECASE)
                if label == text:
                    number_pattern = "|".join(sorted(_NUMBER_WORDS, key=len, reverse=True))
                    label = re.sub(
                        rf"\b(?:at\s+(?:age\s+)?|age\s+)?(?:{number_pattern})(?:[- ](?:{number_pattern}))?(?:\s+years?\s+old)?\b",
                        "",
                        text,
                        count=1,
                        flags=re.IGNORECASE,
                    )
                label = _clean_fragment(label)
                if word_count(label) > 9:
                    label = _clean_fragment(" ".join(label.split()[:9]))
                payload.update({"number": number, "label": label or "Value"})
                if unit:
                    payload["unit"] = unit

        if relation == "cta":
            action_match = re.search(r"\b(visit|book|download|join|subscribe|explore|call|bring|learn more)\b", text, flags=re.IGNORECASE)
            domain_match = re.search(r"\b(?:https?://)?(?:www\.)?[a-z0-9-]+(?:\.[a-z]{2,})(?:/[\w./?=&%-]*)?\b", text, flags=re.IGNORECASE)
            # A CTA must come from the source. Do not invent an action label.
            payload["action"] = _clean_fragment(action_match.group(1)) if action_match else ""
            if domain_match:
                payload["destination"] = domain_match.group(0)

        if relation == "question":
            question = next((p for p in _sentence_parts(text) if p.endswith("?")), None)
            if question:
                payload["headline"] = question

        # Explicit fields always win. Nonvisual control keys are excluded from payload.
        control_keys = {
            "relation", "infographic", "template", "motion", "layout", "density",
            "asset", "scope", "preference", "data", "reduced_motion",
        }
        for key, value in overrides.items():
            if key in control_keys:
                continue
            if key in {"items", "nodes", "children"}:
                payload[key] = _list_value(value)
            elif key == "events" and isinstance(value, list):
                payload[key] = value
            else:
                payload[key] = value

        # Helpful cross-role fallbacks that do not invent text.
        if "items" in payload and relation == "network" and "nodes" not in payload:
            payload["nodes"] = payload["items"]
        if "items" in payload and relation == "hierarchy" and "children" not in payload:
            payload["children"] = payload["items"]
        if relation in {"contrast", "comparison", "transformation", "cause_effect", "problem_solution"}:
            if "left" not in payload or "right" not in payload:
                parts = _sentence_parts(text)
                if len(parts) >= 2:
                    payload.setdefault("left", parts[0])
                    payload.setdefault("right", parts[1])
        return payload
