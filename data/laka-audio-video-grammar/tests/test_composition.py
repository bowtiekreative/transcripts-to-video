"""Composition-level behaviour: carriers, rhythm, accent budget."""
from __future__ import annotations

from pathlib import Path

import yaml

from laka_video.composition import _salient_entities, _shared_entities, apply_composition
from laka_video.ordering import GEOMETRY_FAMILY

ROOT = Path(__file__).resolve().parents[1]
PERCEPTION = yaml.safe_load((ROOT / "grammar" / "perception.yml").read_text(encoding="utf-8"))


def scene(sid, template, payload=None, semantics=None, **kw):
    base = {
        "id": sid, "template": template, "layout": "vertical_rail",
        "payload": payload or {}, "semantics": semantics or {},
        "start": 0.0, "end": 8.0,
        "selection_trace": {"selected": {"order": {"semantic_loss": 0, "false_implication_risk": 0,
                                                   "relation_mismatch": 0, "chunks": 2}},
                            "candidates": []},
    }
    base.update(kw)
    return base


# --------------------------------------------------------------- entities ---
def test_a_scene_is_about_its_proper_nouns_not_its_first_word():
    """The old continuity key was the headline's first content word, which is
    close to a random token; nothing ever matched and persistence sat at 0%."""
    found = _salient_entities(scene("s1", "title_card", {
        "headline": "Souls Matter brings together reviews from disabled people",
    }))
    assert "souls matter" in found


def test_shared_entities_link_adjacent_scenes():
    a = scene("s1", "title_card", {"headline": "We rebuilt HouseSmart from scratch"})
    b = scene("s2", "list_stack", {"headline": "HouseSmart now ships weekly"})
    assert "housesmart" in _shared_entities(a, b)


def test_given_information_counts_as_already_on_screen():
    """The given-new contract: given material may already be from the prior scene."""
    a = scene("s1", "title_card", {"headline": "The migration finished last quarter"})
    b = scene("s2", "list_stack", {"headline": "Two things changed"},
              semantics={"given": "the migration"})
    assert _shared_entities(a, b)


# ---------------------------------------------------------------- carrier ---
def test_same_geometry_carries_even_when_the_subject_changes():
    """"Appear, mutate, transform, exit" is about the OBJECT persisting."""
    scenes = [scene("s1", "before_after"), scene("s2", "problem_solution")]
    apply_composition(scenes, PERCEPTION, 16.0)
    assert scenes[1]["carrier"]["mode"] == "frame"
    assert GEOMETRY_FAMILY["before_after"] == GEOMETRY_FAMILY["problem_solution"] == "pair"


def test_a_different_geometry_does_not_carry():
    scenes = [scene("s1", "before_after"), scene("s2", "list_stack")]
    apply_composition(scenes, PERCEPTION, 16.0)
    assert "carrier" not in scenes[1] or scenes[1].get("carrier") is None


def test_the_report_separates_material_from_compiler():
    """actual == possible means the source has no more continuity to exploit,
    which is a different message from 'the compiler declined to use it'."""
    scenes = [scene("s1", "title_card"), scene("s2", "list_stack"), scene("s3", "network")]
    report = apply_composition(scenes, PERCEPTION, 24.0)
    assert "carrier_opportunities" in report
    assert report["carrier_opportunities"] <= 1.0


# ------------------------------------------------------------ accent budget --
def test_exactly_one_saturated_frame_and_it_is_the_one_with_the_ask():
    scenes = [
        scene("s1", "cta_card", {"headline": "Come along", "action": "Bring"}),
        scene("s2", "cta_card", {"headline": "Start here", "destination": "example.com"}),
        scene("s3", "title_card", {"headline": "The end"}),
    ]
    report = apply_composition(scenes, PERCEPTION, 24.0)
    assert report["accent_bleed_scenes"] == 1
    assert scenes[1]["accent_bleed"] is True, "the destination is the conversion moment"
    assert scenes[0]["accent_bleed"] is False


def test_rhythm_never_buys_a_worse_claim():
    """A demotion may only pick a candidate that is at least as true."""
    dense = scene("s1", "network", {"items": ["a", "b", "c", "d"], "headline": "x"})
    dense["density_level"] = "D3"
    follower = scene("s2", "network", {"items": ["e", "f", "g", "h"], "headline": "y"})
    follower["selection_trace"]["candidates"] = [
        {"template": "title_card", "layout": "vertical_rail",
         "order": {"semantic_loss": 2, "false_implication_risk": 0, "relation_mismatch": 0, "chunks": 2}},
    ]
    apply_composition([dense, follower], PERCEPTION, 16.0)
    assert follower["template"] == "network", "a lossy candidate must not be used to fix rhythm"
