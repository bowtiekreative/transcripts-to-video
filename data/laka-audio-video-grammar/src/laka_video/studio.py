from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import default_grammar_dir, load_yaml


def load_studio_library(grammar_dir: str | Path | None = None) -> dict[str, Any]:
    grammar = Path(grammar_dir).resolve() if grammar_dir else default_grammar_dir()
    return load_yaml(grammar / "studio-library.yml")


def _choice_key(template: str, layout: str) -> str:
    return f"{template}::{layout}"


def _choice(
    template: str,
    layout: str,
    labels: dict[str, str],
    *,
    score: float | None = None,
    recommended: bool = False,
    requires_asset: bool = False,
    description: str = "",
) -> dict[str, Any]:
    label = labels.get(template, template.replace("_", " ").title())
    if layout == "image_overlay":
        label = "Image + headline"
    return {
        "key": _choice_key(template, layout),
        "template": template,
        "layout": layout,
        "label": label,
        "description": description,
        "score": round(float(score), 2) if score is not None else None,
        "recommended": recommended,
        "requires_asset": requires_asset,
    }


def build_studio_review(storyboard: dict[str, Any], library: dict[str, Any]) -> dict[str, Any]:
    labels = {str(k): str(v) for k, v in (library.get("template_labels") or {}).items()}
    studio_cfg = (library.get("modes") or {}).get("studio") or {}
    candidate_limit = max(1, int(studio_cfg.get("candidate_limit", 5)))
    score_band = max(0.0, float(studio_cfg.get("score_band", 16)))
    image_cfg = library.get("image_slide") or {}
    allowed_image_relations = set(image_cfg.get("allowed_relations") or [])
    review_scenes: list[dict[str, Any]] = []

    for index, scene in enumerate(storyboard.get("scenes", []), 1):
        selected = scene.get("selection_trace", {}).get("selected", {}) or {}
        selected_template = str(scene.get("template") or selected.get("template") or "title_card")
        selected_layout = str(scene.get("layout") or selected.get("layout") or "vertical_rail")
        selected_score = float(selected.get("score", 0.0))
        choices: list[dict[str, Any]] = [
            _choice(
                selected_template,
                selected_layout,
                labels,
                score=selected_score,
                recommended=True,
                description="Highest-ranked truth-safe composition.",
            )
        ]
        seen = {choices[0]["key"]}
        candidates = scene.get("selection_trace", {}).get("candidates", []) or []
        for candidate in candidates:
            template = str(candidate.get("template") or "")
            layout = str(candidate.get("layout") or "")
            score = float(candidate.get("score", 0.0))
            key = _choice_key(template, layout)
            if not template or not layout or key in seen or selected_score - score > score_band:
                continue
            choices.append(_choice(template, layout, labels, score=score, description="Valid alternate from the Studio grammar."))
            seen.add(key)
            if len(choices) >= candidate_limit:
                break

        relation = str(scene.get("primary_relation") or "emphasis")
        if relation in allowed_image_relations and not scene.get("data_bound"):
            image_template = str(image_cfg.get("template", "title_card"))
            image_layout = str(image_cfg.get("layout", "image_overlay"))
            image_key = _choice_key(image_template, image_layout)
            if image_key not in seen:
                choices.append(
                    _choice(
                        image_template,
                        image_layout,
                        labels,
                        requires_asset=True,
                        description=str(image_cfg.get("description") or "A required image with protected text."),
                    )
                )

        review_scenes.append(
            {
                "id": str(scene.get("id")),
                "index": index,
                "start": float(scene.get("start", 0.0)),
                "end": float(scene.get("end", 0.0)),
                "text": str(scene.get("text", "")),
                "headline": str(scene.get("payload", {}).get("headline") or scene.get("text", "")),
                "relation": relation,
                "selected": choices[0]["key"],
                "choices": choices,
            }
        )

    return {
        "library": str(library.get("name", "LAVC Studio Library")),
        "version": str(library.get("version", "1.0.0")),
        "principle": str(library.get("principle", "")),
        "scenes": review_scenes,
    }


def allowed_review_choices(review: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        str(scene["id"]): {str(choice["key"]): choice for choice in scene.get("choices", [])}
        for scene in review.get("scenes", [])
    }
