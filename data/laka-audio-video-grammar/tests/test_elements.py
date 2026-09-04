"""The Studio element library, bridged into the compiler.

grammar/studio-library.yml named studio/lavc-elements.js as its source from the
start; the file was never in the repo and the compiler was wired to 23 of its
52 elements.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from laka_video.utils import conform_elements_js, studio_elements_js

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = yaml.safe_load((ROOT / "grammar" / "templates.yml").read_text(encoding="utf-8"))["templates"]
ELEMENT_TEMPLATES = [t for t in TEMPLATES if t.get("element")]


def test_the_library_ships_with_the_package():
    js, counts = studio_elements_js()
    assert js and "LAVC_ELEMENTS" in js
    assert counts, "the conform pass must report what it changed"


def test_the_library_is_conformed_to_the_design_system():
    """The library predates the audit: 30 elements overshoot and 8 rotate."""
    js, counts = studio_elements_js()
    assert counts["overshoot"] == 1, "the single overshoot easing must be replaced"
    assert counts["rotation"] >= 7
    assert "1.70158" not in js, "the overshoot constant must not survive"


def test_colour_is_resolved_at_the_boundary_not_by_rewriting_source():
    """Rewriting `x.c.accent2` produced `x.(c.accentHover||...)` and broke the
    parse. The renderer binds the name on the context object instead."""
    js, _ = studio_elements_js()
    assert "(c.accentHover||c.accent2)" not in js
    renderer = (ROOT / "src" / "laka_video" / "data" / "templates" / "studio-renderer.js").read_text(encoding="utf-8")
    assert "accent2: colors.accentHover" in renderer


def test_an_svg_layout_rotation_survives():
    """The proportion ring rotates its arc start to twelve o'clock. That is
    layout, not motion, and stripping it would break the element."""
    js, _ = studio_elements_js()
    assert 'transform="rotate(-90' in js


def test_conform_is_pure():
    source = "const eb=p=>{p=clamp(p);const c1=1.70158,c3=c1+1;return 1+c3*Math.pow(p-1,3)+c1*Math.pow(p-1,2);};"
    once, _ = conform_elements_js(source)
    twice, _ = conform_elements_js(once)
    assert once == twice, "conforming an already-conformed file must not change it again"


def test_elements_are_registered_in_the_grammar():
    ids = {t["id"] for t in ELEMENT_TEMPLATES}
    for expected in ("caption_only", "strike_through", "parts_diagram", "flow_diagram",
                     "delta", "ranked_bars", "progress_bar"):
        assert expected in ids, f"{expected} exists in the library but the compiler cannot select it"


def test_elements_declare_the_aspects_they_were_authored_for():
    """The library's own context defaults to 1920x1080 and its elements lay out
    horizontally. Rendering one at 9:16 put two small nodes mid-frame."""
    for template in ELEMENT_TEMPLATES:
        assert "9:16" not in template["aspects"], f"{template['id']} is a landscape element"


def test_fit_is_a_condition_of_eligibility():
    """The library was authored against one-to-three word labels; a sentence
    overflows its fixed node boxes at every aspect. An element is offered when
    the content suits it, not repaired afterwards."""
    from laka_video.selector import _slots_fit

    template = next(t for t in ELEMENT_TEMPLATES if t["id"] == "flow_diagram")
    assert template.get("max_words_per_slot")
    fits, _ = _slots_fit(template, {"items": ["Signal", "Detection", "Support"]})
    assert fits
    fits, reason = _slots_fit(template, {"items": ["Look at who it affects", "Signal"]})
    assert not fits and "slot" in reason


def test_a_template_without_a_cap_is_unaffected():
    from laka_video.selector import _slots_fit

    fits, _ = _slots_fit({"id": "title_card"}, {"left": "a very long span of words indeed here"})
    assert fits
