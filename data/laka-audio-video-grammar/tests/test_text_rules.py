from pathlib import Path

from laka_video.text_rules import TextRuleEngine
from laka_video.utils import load_yaml


def engine() -> TextRuleEngine:
    root = Path(__file__).parents[1]
    return TextRuleEngine(load_yaml(root / "grammar" / "lexicon.yml"))


def test_transformation_extracts_literal_pair():
    result = engine().classify("We turn attention into action.")
    assert result["primary_relation"] == "transformation"
    assert result["payload"]["left"] == "Attention"
    assert result["payload"]["right"] == "Action"


def test_written_number_becomes_big_number_payload_without_number_words_in_label():
    result = engine().classify("At forty-one, I was diagnosed with autism and ADHD.")
    assert result["payload"]["number"] == "41"
    assert "forty-one" not in result["payload"]["label"].lower()
    assert "diagnosed" in result["payload"]["label"].lower()


def test_conditional_extracts_condition_and_response():
    result = engine().classify("When the result fails the truth test, the system must use a title card.")
    assert result["primary_relation"] == "conditional"
    assert result["payload"]["left"] == "The result fails the truth test"
    assert result["payload"]["right"] == "The system must use a title card"


def test_single_time_reference_does_not_force_timeline():
    result = engine().classify("At forty-one, I was diagnosed with autism and ADHD.")
    assert result["primary_relation"] != "timeline"


def test_sequence_markers_do_not_leak_into_previous_items():
    result = engine().classify(
        "First, measure the timeline. Next, identify the relationship. Finally, reveal it in order."
    )
    assert result["primary_relation"] == "sequence"
    assert result["payload"]["items"] == [
        "Measure the timeline", "Identify the relationship", "Reveal it in order"
    ]
