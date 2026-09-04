"""The reading budget, payload deduplication and scene segmentation.

Every test here pins a defect that shipped: a measurement that never looked at
half the templates, a payload holding four copies of one sentence, a cut that
stranded a subordinator, and scenes that could not span a subtitle boundary.
"""
from __future__ import annotations

import yaml
from pathlib import Path

import pytest

from laka_video.budget import _headline_trim, dedupe_payload, fit_payload_to_budget
from laka_video.ordering import RENDERED_FIELDS, visible_words_for

ROOT = Path(__file__).resolve().parents[1]
PERCEPTION = yaml.safe_load((ROOT / "grammar" / "perception.yml").read_text(encoding="utf-8"))


# ------------------------------------------------------------ measurement ---
def test_every_template_is_measured():
    """The budget runs before selection, so it must bound the heaviest outcome.

    Sampling four templates meant `nodes`, `children`, `events` and `series`
    were never measured at all, and a scene that became a network carried 42
    words with no trimming applied.
    """
    # Each list-bearing field must be visible to the template that renders it.
    cases = {
        "nodes": "network",
        "items": "list_stack",
        "events": "timeline",
        "children": "hierarchy_tree",
        "series": "bar_chart",
    }
    for field, template in cases.items():
        entries = ([{"event": "one two three", "time": "2020"}] if field == "events"
                   else [{"label": "one two three", "value": 1}] if field == "series"
                   else ["one two three", "four five six"])
        payload = {"headline": "a b", field: entries}
        assert visible_words_for(template, payload) > 2, \
            f"{template} renders {field} but the measurement cannot see it"


def test_visible_words_counts_only_what_the_template_renders():
    payload = {"headline": "one two three", "left": "four five", "right": "six seven",
               "items": ["eight nine", "ten eleven"]}
    # A title card shows the headline; it does not show the pair or the list.
    assert visible_words_for("title_card", payload) == 3


# ----------------------------------------------------------- deduplication ---
def test_alternate_encodings_of_one_sentence_collapse():
    line = "It's my framework for living documents that can evolve"
    payload = {"headline": line, "center": line, "nodes": [line, "Connect their sources"],
               "items": [line, "Connect their sources"]}
    removed = dedupe_payload(payload)
    assert removed, "four copies of one sentence must not survive"
    assert "items" not in payload or payload.get("items") != payload.get("nodes")
    assert "center" not in payload, "a hub restating the headline is not a second mark"
    assert all("framework for living documents" not in str(n) for n in payload.get("nodes", []))


def test_a_time_column_that_never_changes_is_dropped():
    payload = {"events": [{"time": "When", "event": "a rule helps"},
                          {"time": "When", "event": "the situation changes"}]}
    dedupe_payload(payload)
    assert all("time" not in e for e in payload["events"]), \
        "a word repeated down the side of the frame is not an axis"


def test_a_real_time_column_survives():
    payload = {"events": [{"time": "2019", "event": "first release"},
                          {"time": "2024", "event": "rebuild"}]}
    dedupe_payload(payload)
    assert all(e.get("time") for e in payload["events"])


# ------------------------------------------------------------- trim safety ---
@pytest.mark.parametrize(
    "text",
    [
        "When a rule helps, we should understand why",
        "If the situation changes, we should know what to change",
        "Because the system failed, everyone stopped trusting it",
    ],
)
def test_a_cut_never_strands_a_subordinator(text):
    """"When a rule helps" is a question the frame never answers."""
    assert _headline_trim(text, 4) == text


def test_no_cut_without_a_clause_boundary():
    """Cutting on word count alone produced "I'm a cognitive"."""
    text = "I am a cognitive architect and innovation strategist"
    assert _headline_trim(text, 4) == text


def test_a_real_clause_boundary_is_used():
    text = "The service shipped on time, and the team took a week off"
    assert _headline_trim(text, 6) == "The service shipped on time"


# ---------------------------------------------------------------- budget ----
def test_supporting_copy_goes_before_anything_else():
    payload = {"headline": "one two three four five", "supporting": "a much longer restatement of it all",
               "items": ["alpha beta", "gamma delta"]}
    record = fit_payload_to_budget(payload, "one two three four five", 4.0, PERCEPTION)
    assert "supporting" not in payload
    assert any("supporting" in r for r in record["removals"])


def test_the_budget_reports_rather_than_breaking_a_sentence():
    """Over budget with nothing safe to cut is a reported gap, not a fragment."""
    payload = {"headline": "I am a cognitive architect and innovation strategist"}
    fit_payload_to_budget(payload, payload["headline"], 3.0, PERCEPTION)
    assert payload["headline"] == "I am a cognitive architect and innovation strategist"
