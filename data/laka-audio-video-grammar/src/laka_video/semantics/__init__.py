"""Linguistic analysis: relation, role structure, aspect, modality, depiction.

Static lexical resources only — no model, no inference, no network. The same
transcript always resolves to the same analysis.
"""
from .analysis import SemanticAnalysis, analyze
from .lexicon import Lexicon, load_lexicon

__all__ = ["SemanticAnalysis", "analyze", "Lexicon", "load_lexicon"]
