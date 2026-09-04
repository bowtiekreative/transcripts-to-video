"""Linguistic analysis: relation, role structure, aspect, modality, depiction,
and the EventMath event object the rest of the stack speaks.

Static lexical resources only — no model, no inference, no network. The same
transcript always resolves to the same analysis.
"""
from .analysis import SemanticAnalysis, analyze
from .eventmath import Event, extract_event
from .lexicon import Lexicon, load_lexicon

__all__ = ["SemanticAnalysis", "analyze", "Event", "extract_event", "Lexicon", "load_lexicon"]
