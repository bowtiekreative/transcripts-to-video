from pathlib import Path

from laka_video.lint import lint_storyboard
from laka_video.studio import build_studio_review
from laka_video.utils import load_yaml


def test_studio_review_adds_a_gated_image_choice_only_to_safe_relations():
    root = Path(__file__).parents[1]
    library = load_yaml(root / "grammar" / "studio-library.yml")
    storyboard = {
        "scenes": [
            {
                "id": "scene-001",
                "start": 0,
                "end": 6,
                "text": "Welcome to the film.",
                "primary_relation": "identity",
                "template": "title_card",
                "layout": "vertical_rail",
                "payload": {"headline": "Welcome to the film"},
                "selection_trace": {
                    "selected": {"template": "title_card", "layout": "vertical_rail", "score": 90},
                    "candidates": [],
                },
            },
            {
                "id": "scene-002",
                "start": 6,
                "end": 12,
                "text": "The value increased to 62 percent.",
                "primary_relation": "quantity",
                "template": "big_number",
                "layout": "number_rail",
                "payload": {"headline": "The value increased", "number": "62%", "label": "share"},
                "data_bound": True,
                "selection_trace": {
                    "selected": {"template": "big_number", "layout": "number_rail", "score": 94},
                    "candidates": [],
                },
            },
        ]
    }

    review = build_studio_review(storyboard, library)

    assert any(choice["requires_asset"] for choice in review["scenes"][0]["choices"])
    assert not any(choice["requires_asset"] for choice in review["scenes"][1]["choices"])


def test_image_layout_is_a_blocking_lint_error_until_filled():
    storyboard = {
        "composition": {"duration": 6},
        "captions": [],
        "scenes": [
            {
                "id": "scene-001",
                "start": 0,
                "end": 6,
                "text": "A visual claim.",
                "primary_relation": "identity",
                "template": "title_card",
                "layout": "image_overlay",
                "payload": {"headline": "A visual claim"},
                "motion": {},
            }
        ],
    }
    defaults = {
        "text": {"max_words_on_screen": 18},
        "timing": {"min_scene_seconds": 3.5, "max_scene_seconds": 12, "min_resolve_seconds": 0.8},
    }
    templates = {
        "templates": [
            {
                "id": "title_card",
                "relations": {"identity": 1},
                "required_all": ["headline"],
            }
        ]
    }

    blocked = lint_storyboard(storyboard, defaults, templates)
    assert blocked["status"] == "fail"
    assert any(issue["code"] == "asset.required" for issue in blocked["issues"])

    storyboard["scenes"][0]["asset"] = "assets/scene-001.png"
    allowed = lint_storyboard(storyboard, defaults, templates)
    assert allowed["status"] == "pass"
