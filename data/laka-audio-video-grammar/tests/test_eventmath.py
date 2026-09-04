"""EventMath 2.0 extraction — the vocabulary the rest of the stack speaks.

Everything is an event: who + what + where + when + why + how, seven universal
elements, and a LENS x DIRECTION x QUANTIFIER triple.
"""
from __future__ import annotations

import pytest

from laka_video.semantics import extract_event, load_lexicon


@pytest.fixture(scope="module")
def vocab():
    return load_lexicon().eventmath


def ev(text, payload=None, speaker=None, vocab=None):
    return extract_event(text, payload or {}, vocab, None, speaker=speaker)


# ---------------------------------------------------------------- the triple ---
@pytest.mark.parametrize(
    ("text", "direction"),
    [
        ("Revenue grew every quarter.", "more_same"),
        ("Headcount fell after the merger.", "less_same"),
        ("We shipped weekly, but nobody noticed.", "indirect_opposite"),
        ("The outage caused every ticket that week.", "direct"),
        ("The service costs three hundred dollars.", "keep_same"),
    ],
)
def test_direction_is_read_from_the_motion(text, direction, vocab):
    assert ev(text, vocab=vocab).direction == direction


@pytest.mark.parametrize(
    ("text", "quantifier"),
    [
        ("Not all customers agreed.", "partial"),
        ("No one agreed.", "none"),
        ("Every customer agreed.", "all"),
        ("Some of the team agreed.", "partial"),
    ],
)
def test_quantifier_is_a_claim_about_scope(text, quantifier, vocab):
    assert ev(text, vocab=vocab).quantifier == quantifier


def test_not_all_is_partial_not_none(vocab):
    """The partial group survives. Reading it as `none` negates a group the
    speaker explicitly left standing — the same scope error negation.yml guards."""
    assert ev("Not all customers agreed.", vocab=vocab).quantifier == "partial"


def test_cardinality_anchors_the_quantifier(vocab):
    """Four peers on screen is `many` whatever the sentence says, so the
    quantifier and the topology table cannot disagree about one scene."""
    event = ev("The projects continued.", {"items": ["a", "b", "c", "d"]}, vocab=vocab)
    assert event.quantifier == "many"


def test_scope_words_outrank_cardinality(vocab):
    """"Not all of them" stays partial even with four names drawn."""
    event = ev("Not all of them agreed.", {"items": ["a", "b", "c", "d"]}, vocab=vocab)
    assert event.quantifier == "partial"


# ------------------------------------------------------------------- 5W+H ---
def test_gaps_are_reported_never_filled(vocab):
    event = ev("Something changed.", vocab=vocab)
    assert "where" in event.gaps and "when" in event.gaps
    assert event.where is None and event.when is None
    assert event.origin == "stated"


def test_virtual_location_resolves_before_geographic(vocab):
    """Otherwise "Alberta" matches before "Zoom" in a sentence holding both."""
    assert ev("The Alberta team met on Zoom.", vocab=vocab).where == "Zoom"


def test_first_person_resolves_to_the_known_speaker(vocab):
    """Stated context from the project, not a filled gap: the transcript is them."""
    event = ev("I was diagnosed at forty-one.", speaker="Ryan Perez", vocab=vocab)
    assert event.who == "Ryan Perez"
    assert "who" not in event.gaps


def test_a_named_actor_wins_over_the_speaker(vocab):
    event = ev("Dr. Antoinette Peragine presented the findings.", speaker="Ryan Perez", vocab=vocab)
    assert event.who and "Antoinette" in event.who


# --------------------------------------------------------------- elements ---
def test_a_begin_state_without_an_end_state_is_dropped(vocab):
    """An incomplete transformation must not be drawn as a pair: the missing
    half would be invented."""
    event = ev("It started badly.", {"left": "a bad start"}, vocab=vocab)
    assert "begin_state" not in event.elements


def test_a_complete_pair_survives(vocab):
    event = ev("We went from a spreadsheet to a dashboard.",
               {"left": "a spreadsheet", "right": "a dashboard"}, vocab=vocab)
    assert "begin_state" in event.elements and "end_state" in event.elements


def test_elements_are_discriminated_not_stamped(vocab):
    """objects, actions and tools all read `items`; without a language test
    every list claimed to be all three at once."""
    event = ev("The projects continued.", {"items": ["a", "b", "c"]}, vocab=vocab)
    assert "objects" in event.elements
    assert "tools" not in event.elements


def test_events_are_not_stringified_dicts(vocab):
    event = ev("First we look, then we build.",
               {"events": [{"time": "2020", "event": "we looked"}]}, vocab=vocab)
    for values in event.elements.values():
        assert all(not str(v).startswith("{'") for v in values)


# --------------------------------------------------------- classification ---
@pytest.mark.parametrize(
    ("text", "category"),
    [
        ("What could we build from this?", "question"),
        ("We should understand why.", "decision"),
        ("I think the system is wrong.", "belief"),
        ("The service costs three hundred dollars.", "fact"),
    ],
)
def test_category_classification(text, category, vocab):
    assert ev(text, vocab=vocab).category == category


def test_discourse_filler_is_noise(vocab):
    """A segment carrying no proposition earns a caption and nothing else."""
    assert ev("So, anyway.", vocab=vocab).signal is False
    assert ev("We rebuilt the whole system.", vocab=vocab).signal is True


def test_extraction_is_deterministic(vocab):
    text = "Dr. Antoinette Peragine presented in Calgary because the data changed."
    assert ev(text, vocab=vocab).to_dict() == ev(text, vocab=vocab).to_dict()
