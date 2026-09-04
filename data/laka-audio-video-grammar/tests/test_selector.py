from pathlib import Path

from laka_video.selector import TemplateSelector
from laka_video.text_rules import TextRuleEngine
from laka_video.utils import load_yaml


def fixtures():
    root = Path(__file__).parents[1]
    defaults = load_yaml(root / "grammar" / "defaults.yml")
    brand = load_yaml(root / "grammar" / "brand.example.yml")
    templates = load_yaml(root / "grammar" / "templates.yml")
    engine = TextRuleEngine(load_yaml(root / "grammar" / "lexicon.yml"))
    return engine, TemplateSelector(templates, defaults, brand)


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
