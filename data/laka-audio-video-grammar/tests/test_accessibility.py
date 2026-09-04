"""Accessibility as a hard gate (nd-ux; MOTION_MATH §7).

This compiler puts a neurodivergent speaker's own words on screen, so "reduce
cognitive load first" is the brief rather than a compliance checkbox.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from laka_video.accessibility import (
    apply_reduced_motion, audit_contrast, audit_motion, contrast_ratio,
    flesch_kincaid_grade, parse_colour, relative_luminance,
)

ROOT = Path(__file__).resolve().parents[1]
PERCEPTION = yaml.safe_load((ROOT / "grammar" / "perception.yml").read_text(encoding="utf-8"))
BRAND = yaml.safe_load((ROOT / "grammar" / "brand.example.yml").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ colour ---
def test_contrast_matches_the_wcag_reference_values():
    assert contrast_ratio("#FFFFFF", "#000000") == pytest.approx(21.0, abs=0.01)
    assert contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21.0, abs=0.01)
    assert contrast_ratio("#777777", "#FFFFFF") == pytest.approx(4.48, abs=0.05)


def test_a_translucent_colour_is_composited_before_measuring():
    """A hairline at 8% alpha does not have the contrast of white, and scoring
    it as white would pass a line nobody can see."""
    solid = contrast_ratio("#F5F7FA", "#07090D")
    faint = contrast_ratio("rgba(245,247,250,0.08)", "#07090D")
    assert faint is not None and solid is not None
    assert faint < solid / 4


def test_the_shipped_palette_passes_wcag_aa_everywhere_it_is_drawn():
    """Checked on the pairs the renderer actually puts together, not on the
    palette in the abstract — that would pass colours that never touch."""
    failures = [f for f in audit_contrast(BRAND, PERCEPTION) if not f["passes"]]
    assert not failures, f"contrast failures: {failures}"


def test_the_audit_covers_the_accent_frame():
    pairs = {f["pair"] for f in audit_contrast(BRAND, PERCEPTION)}
    assert "on_accent on accent" in pairs, "the one saturated frame must be checked too"


# -------------------------------------------------------------- vestibular ---
def test_camera_drift_stays_under_the_depth_threshold():
    story = {
        "scenes": [{
            "id": "s1", "start": 0.0, "end": 8.0,
            "motion": {"parameters": {"camera_drift": True, "energy": 1.0}},
        }],
    }
    failures = [f for f in audit_motion(story, PERCEPTION) if not f["passes"]]
    assert not failures


def test_a_very_short_scene_is_flagged_as_a_flicker():
    story = {"scenes": [{"id": "s1", "start": 0.0, "end": 0.2, "motion": {}}]}
    flash = [f for f in audit_motion(story, PERCEPTION) if f["check"] == "flash_rate"]
    assert flash and not flash[0]["passes"]


# ---------------------------------------------------------- reduced motion ---
def test_a_reduced_cut_keeps_the_edit_and_drops_the_movement():
    story = {
        "composition": {"duration": 10.0},
        "scenes": [{
            "id": "s1", "start": 0.0, "end": 10.0, "text": "unchanged",
            "payload": {"headline": "unchanged"},
            "motion": {"parameters": {"camera_drift": True, "travel_px": 40}},
            "semantics": {"motion_operator": "loop"},
        }],
    }
    reduced = apply_reduced_motion(story)
    assert reduced["composition"]["reduced_motion"] is True
    scene = reduced["scenes"][0]
    # Same edit: same boundaries, same words.
    assert (scene["start"], scene["end"]) == (0.0, 10.0)
    assert scene["payload"]["headline"] == "unchanged"
    # No movement.
    assert scene["motion"]["parameters"]["camera_drift"] is False
    assert scene["motion"]["parameters"]["travel_px"] == 0
    assert scene["semantics"]["motion_operator"] == "static"
    assert scene["semantics"]["motion_operator_reduced_from"] == "loop"


def test_reducing_does_not_mutate_the_original():
    story = {"composition": {}, "scenes": [
        {"id": "s1", "motion": {"parameters": {"camera_drift": True}}, "semantics": {}},
    ]}
    apply_reduced_motion(story)
    assert story["scenes"][0]["motion"]["parameters"]["camera_drift"] is True


def test_the_renderer_honours_the_flag():
    player = (ROOT / "src" / "laka_video" / "data" / "templates" / "player.html.j2").read_text(encoding="utf-8")
    renderer = (ROOT / "src" / "laka_video" / "data" / "templates" / "studio-renderer.js").read_text(encoding="utf-8")
    assert "C.reduced_motion" in player, "the dolly is motion too"
    assert "REDUCED_MOTION" in renderer


# ------------------------------------------------------------ plain language --
def test_reading_grade_tracks_sentence_and_word_complexity():
    simple = flesch_kincaid_grade("The team shipped the app. It works well now.")
    dense = flesch_kincaid_grade(
        "The organisational transformation necessitated comprehensive reconsideration "
        "of institutional accessibility methodologies."
    )
    assert simple is not None and dense is not None
    assert simple < 8 < dense


def test_empty_text_has_no_grade():
    assert flesch_kincaid_grade("") is None


def test_luminance_ordering_is_sane():
    assert relative_luminance(parse_colour("#FFFFFF")) > relative_luminance(parse_colour("#808080"))
    assert relative_luminance(parse_colour("#808080")) > relative_luminance(parse_colour("#000000"))


# --------------------------------------------------- the right instrument ---
def test_a_short_label_is_not_measured_as_prose():
    """Flesch-Kincaid on a four-word label reports grade 21 for
    "Difficult experiences -> Constructive action", which is a property of the
    formula, not of the copy."""
    from laka_video.accessibility import reading_difficulty

    measure, _ = reading_difficulty("Difficult experiences Constructive action")
    assert measure == "syllables_per_word"


def test_running_prose_is_measured_as_prose():
    from laka_video.accessibility import reading_difficulty

    measure, value = reading_difficulty(
        "All Inclusive Websites focuses on accessibility-first web design for everyone"
    )
    assert measure == "grade" and value > 12


def test_lexical_density_separates_plain_from_technical():
    from laka_video.accessibility import lexical_density

    assert lexical_density("We start with what is happening") < 1.6
    assert lexical_density("Organisational accessibility methodologies") > 4.0
