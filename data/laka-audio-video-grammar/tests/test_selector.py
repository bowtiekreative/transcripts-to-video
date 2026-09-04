from pathlib import Path

from laka_video.selector import TemplateSelector
from laka_video.text_rules import TextRuleEngine
from laka_video.utils import load_yaml


def fixtures():
    root = Path(__file__).parents[1]
    defaults = load_yaml(root / "grammar" / "defaults.yml")
    brand = load_yaml(root / "grammar" / "brand.example.yml")
    templates = load_yaml(root / "grammar" / "templates.yml")
    studio = load_yaml(root / "grammar" / "studio-library.yml")
    engine = TextRuleEngine(load_yaml(root / "grammar" / "lexicon.yml"))
    return engine, TemplateSelector(templates, defaults, brand, studio)


def choose(text: str):
    engine, selector = fixtures()
    analysis = engine.classify(text)
    scene = {
        "id": "s1", "start": 0.0, "end": 7.0, "words_per_second": 2.0,
        "audio_features": {"mean_energy": 0.5}, "continuity_key": "test",
    }
    return selector.select(analysis, scene, {"aspect": "9:16"}, [], 33)[0]


def test_selector_is_repeatable():
    a = choose("We turn attention into action.")
    b = choose("We turn attention into action.")
    assert (a.template, a.layout, a.score) == (b.template, b.layout, b.score)
    assert a.template == "transformation_arrow"


def test_condition_selects_condition_cards():
    selected = choose("If a chart has no values, the system must reject the chart.")
    assert selected.template == "condition_cards"


def test_wildcard_is_seeded_and_stays_inside_valid_candidate_pool():
    engine, selector = fixtures()
    analysis = engine.classify("We turn attention into action.")
    scene = {
        "id": "s1", "start": 0.0, "end": 7.0, "words_per_second": 2.0,
        "audio_features": {"mean_energy": 0.5}, "continuity_key": "test",
    }
    first, candidates = selector.select(
        analysis, scene, {"aspect": "16:9"}, [], 812, context={"selection_mode": "wildcard"}
    )
    repeated, _ = selector.select(
        analysis, scene, {"aspect": "16:9"}, [], 812, context={"selection_mode": "wildcard"}
    )

    assert (first.template, first.layout) == (repeated.template, repeated.layout)
    assert (first.template, first.layout) in {(candidate.template, candidate.layout) for candidate in candidates[:3]}
    assert any("wildcard" in reason for reason in first.reasons)
