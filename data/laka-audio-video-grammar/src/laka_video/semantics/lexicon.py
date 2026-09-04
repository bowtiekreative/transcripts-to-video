"""Loaders for the linguistic resources under grammar/lexicon/.

Everything here is static data read from disk. There is no model, no inference
and no network call, so the same transcript always resolves to the same
analysis — which is the whole premise of the compiler.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..utils import default_grammar_dir, load_yaml


def lexicon_dir(grammar_dir: str | Path | None = None) -> Path:
    base = Path(grammar_dir).resolve() if grammar_dir else default_grammar_dir()
    return base / "lexicon"


def _compile_all(patterns: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(p, flags=re.IGNORECASE) for p in patterns or []]


@dataclass(frozen=True)
class SchemaRule:
    id: str
    label: str
    diagram: str
    template: str | None
    needs_element: str | None
    entities: tuple[str, ...]
    patterns: tuple[re.Pattern[str], ...]


@dataclass(frozen=True)
class FrameRule:
    id: str
    evoked_by: frozenset[str]
    roles: dict[str, dict[str, Any]]
    schema: str | None
    requires_numeric: bool


@dataclass
class Lexicon:
    """Every lexical resource, compiled once."""

    schemas: list[SchemaRule] = field(default_factory=list)
    frames: list[FrameRule] = field(default_factory=list)
    frame_index: dict[str, FrameRule] = field(default_factory=dict)
    aspect_classes: dict[str, Any] = field(default_factory=dict)
    aspect_signals: dict[str, Any] = field(default_factory=dict)
    modality_levels: dict[str, Any] = field(default_factory=dict)
    negation: dict[str, Any] = field(default_factory=dict)
    metaphors: dict[str, Any] = field(default_factory=dict)
    concreteness: dict[str, float] = field(default_factory=dict)
    concreteness_bands: dict[str, set[str]] = field(default_factory=dict)
    concreteness_thresholds: dict[str, float] = field(default_factory=dict)
    obligation_policy: dict[str, Any] = field(default_factory=dict)
    eventmath: dict[str, Any] = field(default_factory=dict)
    # lemma -> pattern that must also match for the lemma to evoke its frame.
    frame_constraints: dict[str, re.Pattern[str]] = field(default_factory=dict)

    def concreteness_of(self, word: str) -> tuple[str, float | None]:
        """Return (band, rating). Rating is None when only a band is known.

        An unknown word returns ("unknown", None) and the caller must abstain:
        guessing a band for an unrated word is how a compiler ends up putting a
        photograph next to an abstract noun.
        """
        w = (word or "").strip().lower()
        if not w:
            return ("unknown", None)
        if w in self.concreteness:
            value = self.concreteness[w]
            concrete = float(self.concreteness_thresholds.get("concrete", 4.0))
            semi = float(self.concreteness_thresholds.get("semi", 2.5))
            band = "concrete" if value >= concrete else "semi" if value >= semi else "abstract"
            return (band, value)
        for band, words in self.concreteness_bands.items():
            if w in words:
                return (band, None)
        return ("unknown", None)


def _load_concreteness_full(path: Path) -> dict[str, float]:
    """Read the full Brysbaert table if the operator has supplied it."""
    ratings: dict[str, float] = {}
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            header = handle.readline().rstrip("\n").split("\t")
            try:
                word_at = header.index("Word")
                conc_at = header.index("Conc.M")
                bigram_at = header.index("Bigram")
            except ValueError:
                return {}
            for line in handle:
                parts = line.rstrip("\n").split("\t")
                if len(parts) <= max(word_at, conc_at, bigram_at):
                    continue
                if parts[bigram_at] != "0":
                    continue
                try:
                    ratings[parts[word_at].strip().lower()] = float(parts[conc_at])
                except ValueError:
                    continue
    except OSError:
        return {}
    return ratings


@lru_cache(maxsize=8)
def load_lexicon(grammar_dir: str | None = None) -> Lexicon:
    root = lexicon_dir(grammar_dir)
    lex = Lexicon()

    # --- image schemas ------------------------------------------------------
    schema_doc = load_yaml(root / "image_schemas.yml") if (root / "image_schemas.yml").exists() else {}
    definitions = schema_doc.get("schemas", {}) or {}
    order = schema_doc.get("precedence") or list(definitions)
    for schema_id in order:
        spec = definitions.get(schema_id)
        if not spec:
            continue
        patterns: list[str] = []
        for group in ("preposition", "verb", "construction"):
            patterns.extend((spec.get("triggers") or {}).get(group, []) or [])
        lex.schemas.append(
            SchemaRule(
                id=schema_id,
                label=str(spec.get("label", schema_id)),
                diagram=str(spec.get("diagram", "")),
                template=spec.get("template"),
                needs_element=spec.get("needs_element"),
                entities=tuple(spec.get("entities") or []),
                patterns=tuple(_compile_all(patterns)),
            )
        )

    # --- frames -------------------------------------------------------------
    frame_doc = load_yaml(root / "frames.yml") if (root / "frames.yml").exists() else {}
    for frame_id, spec in (frame_doc.get("frames", {}) or {}).items():
        rule = FrameRule(
            id=frame_id,
            evoked_by=frozenset(str(v).lower() for v in (spec.get("evoked_by") or [])),
            roles=spec.get("roles", {}) or {},
            schema=spec.get("schema"),
            requires_numeric=bool(spec.get("requires_numeric")),
        )
        lex.frames.append(rule)
        for verb in rule.evoked_by:
            lex.frame_index.setdefault(verb, rule)
    lex.obligation_policy = frame_doc.get("obligation_policy", {}) or {}
    lex.frame_constraints = {
        str(lemma).lower(): re.compile(pattern, flags=re.IGNORECASE)
        for lemma, pattern in (frame_doc.get("constraints", {}) or {}).items()
    }

    # --- aspect, modality, negation, metaphor -------------------------------
    aspect_doc = load_yaml(root / "aspect.yml") if (root / "aspect.yml").exists() else {}
    lex.aspect_classes = aspect_doc.get("classes", {}) or {}
    lex.aspect_signals = aspect_doc.get("signals", {}) or {}
    lex.modality_levels = (load_yaml(root / "modality.yml") if (root / "modality.yml").exists() else {}).get("levels", {}) or {}
    lex.negation = load_yaml(root / "negation.yml") if (root / "negation.yml").exists() else {}
    lex.metaphors = load_yaml(root / "metaphors.yml") if (root / "metaphors.yml").exists() else {}
    lex.eventmath = load_yaml(root / "eventmath.yml") if (root / "eventmath.yml").exists() else {}

    # --- concreteness -------------------------------------------------------
    core = load_yaml(root / "concreteness_core.yml") if (root / "concreteness_core.yml").exists() else {}
    lex.concreteness_thresholds = core.get("thresholds", {}) or {"concrete": 4.0, "semi": 2.5}
    lex.concreteness_bands = {
        band: {str(w).lower() for w in words}
        for band, words in (core.get("bands", {}) or {}).items()
    }
    full_path = os.environ.get("LAVC_CONCRETENESS_PATH")
    candidate = Path(full_path).expanduser() if full_path else root / "concreteness.txt"
    if candidate.is_file():
        lex.concreteness = _load_concreteness_full(candidate)
    return lex
