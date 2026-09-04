"""The linguistic layer: relation, roles, aspect, modality, depiction.

Each test pins a claim from SEMANTIC_MAPPING.md, and several pin a specific
false positive that the first implementation actually produced.
"""
from __future__ import annotations

import pytest

from laka_video.semantics import analyze, load_lexicon


@pytest.fixture(scope="module")
def lex():
    return load_lexicon()


# ------------------------------------------------------- §2 image schemas ---
@pytest.mark.parametrize(
    ("text", "schema"),
    [
        ("We went from a spreadsheet to a live dashboard.", "source_path_goal"),
        ("The outage drove every support ticket that week.", "force"),
        ("Their policy prevented the team from shipping.", "blockage"),
        ("Each release feeds back into the next one every quarter.", "cycle"),
        ("The budget is divided into four programmes.", "splitting"),
        ("Everything connects to the same knowledge graph.", "link"),
        ("Revenue rose sharply after launch.", "scale"),
    ],
)
def test_schema_comes_from_the_relation_not_the_noun(text, schema, lex):
    assert analyze(text, lex).schema == schema


def test_the_noun_never_selects_the_schema(lex):
    """Same noun, different relation, different diagram."""
    a = analyze("The network connects every team.", lex)
    b = analyze("The network grew from 40 to 400 nodes.", lex)
    assert a.schema == "link"
    assert b.schema in {"source_path_goal", "scale"}


# -------------------------------------------------------------- §3 frames ---
def test_frame_fills_only_the_roles_the_text_filled(lex):
    result = analyze("Sales increased by 37% after the campaign.", lex)
    assert result.frame == "change_position_on_a_scale"
    assert result.roles.get("item") == "Sales"
    assert result.roles.get("difference") == "37%"
    # No initial value was stated, so it must stay unfilled: a template that
    # invents a before-bar is fabricating a baseline the speaker never gave.
    assert "initial_value" not in result.roles


def test_unfilled_core_role_is_reported_not_invented(lex):
    result = analyze("It prevented them from getting through the door.", lex)
    assert result.frame == "preventing"
    assert "preventing_cause" in result.unfilled_core_roles


def test_one_span_does_not_fill_two_roles(lex):
    result = analyze("Disbelief leads to withdrawal.", lex)
    spans = list(result.roles.values())
    assert len(spans) == len(set(spans)), f"a span was reused across roles: {result.roles}"


def test_ambiguous_lemma_needs_its_construction(lex):
    """'potential leads' is a noun. Without the guard it evoked CAUSATION and
    handed the compiler two sentence fragments as a cause and an effect."""
    noun = analyze("Goose Caboose looks for potential leads that marketing left behind.", lex)
    verb = analyze("Poor onboarding leads to churn.", lex)
    assert noun.frame != "causation"
    assert verb.frame == "causation"


def test_time_label_must_look_like_a_time(lex):
    """'increased by 37%' once produced initial_time='by 37'."""
    result = analyze("Sales increased by 37% after the campaign.", lex)
    assert result.roles.get("initial_time", "") in {"after the campaign", ""}


# -------------------------------------------------------------- §5 aspect ---
@pytest.mark.parametrize(
    ("text", "aspect", "operator"),
    [
        ("At forty-one I was diagnosed with autism.", "achievement", "cut"),
        ("They built the whole system from scratch.", "accomplishment", "build_settle"),
        ("The rumour kept spreading through the office.", "activity", "loop"),
        ("The service costs three hundred dollars.", "state", "static"),
    ],
)
def test_aspect_decides_the_motion_operator(text, aspect, operator, lex):
    result = analyze(text, lex)
    assert (result.aspect, result.motion_operator) == (aspect, operator)


# ------------------------------------------------------------ §7 modality ---
def test_hedged_quantity_never_renders_at_full_precision(lex):
    result = analyze("An estimated 96 percent of the audience never complained.", lex)
    assert result.modality == "approximate"
    assert result.label_precision == "rounded"


def test_forecast_is_dashed(lex):
    result = analyze("Revenue will reach four million by 2027.", lex)
    assert result.modality == "forecast"
    assert result.modality_render.get("stroke") == "dashed"


def test_attributed_claim_requires_a_source_label(lex):
    result = analyze("According to the audit, the backlog doubled.", lex)
    assert result.modality == "attributed"
    assert result.modality_render.get("source_label_required") is True


# ------------------------------------------------------------ §8 negation ---
def test_negation_is_shown_then_struck_not_omitted(lex):
    result = analyze("We did not ship the feature.", lex)
    assert result.negation is not None
    assert result.negation["show_positive_first"] is True
    assert result.negation["element"] == "strike_through"


def test_negation_scope_is_preserved(lex):
    """These have different truth conditions. Crossing out the whole group in
    the first case is a factual error, not a style choice."""
    partial = analyze("Not all customers agreed with the change.", lex)
    assert partial.negation["target"] == "quantifier"
    assert partial.negation["survives"] == "partial_group"


# ---------------------------------------------------- §4 depiction gate -----
def test_abstract_head_noun_gets_no_object_depiction(lex):
    assert analyze("Their credibility never recovered.", lex).depiction in {"typography", "schematic"}


def test_concrete_relation_licenses_a_diagram_over_abstract_entities(lex):
    """Schema concreteness and referent concreteness are separate tests."""
    result = analyze("Disbelief leads to withdrawal.", lex)
    assert result.schema == "force"
    assert result.depiction == "schematic"


def test_modal_verbs_are_never_the_head_noun(lex):
    """'can' and 'will' carry a dominant NOUN part of speech in the norms, so
    'a framework that can evolve' once resolved its head to a tin can and
    licensed a photograph."""
    result = analyze("It's my framework for living documents that can evolve.", lex)
    assert result.head_noun not in {"can", "will", "may", "might"}


def test_unknown_word_abstains_rather_than_guessing(lex):
    band, rating = lex.concreteness_of("zzzzquux")
    assert band == "unknown" and rating is None


# ------------------------------------------------- §6 information structure --
def test_contrast_puts_the_focus_on_the_second_half(lex):
    result = analyze("Not a resilience talk, but a build manual.", lex)
    assert result.focus and "build manual" in result.focus
    assert result.given and "resilience" in result.given


# --------------------------------------------------------- §1 metaphor ------
def test_primary_metaphor_licenses_spatial_encoding(lex):
    result = analyze("Costs rose every quarter.", lex)
    assert "vertical_position" in result.metaphor_licences


def test_cultural_metaphor_is_flagged_not_licensed(lex):
    result = analyze("We are like a family here.", lex)
    assert "organisation_is_family" in result.cultural_metaphors
    assert not result.metaphor_licences


# ------------------------------------------------------------ determinism ---
def test_analysis_is_deterministic(lex):
    text = "Their policy prevented the team from shipping until the audit closed."
    assert analyze(text, lex).to_dict() == analyze(text, lex).to_dict()
