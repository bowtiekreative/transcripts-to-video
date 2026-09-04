"""Guards for the design-system contract the renderer is required to hold to.

These are not style preferences. Each one corresponds to a defect that shipped
in rendered frames: a fallback typeface, an off-token colour, a bouncing ease, a
headline cut mid-preposition, or a spoken web address printed as prose.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from laka_video.utils import default_font_dir, inline_font_face_css, normalize_spoken_domains

PACKAGE = Path(__file__).resolve().parents[1] / "src" / "laka_video"
TEMPLATES = PACKAGE / "data" / "templates"
GRAMMAR_SOURCE = Path(__file__).resolve().parents[1] / "grammar"
GRAMMAR_PACKAGED = PACKAGE / "data" / "grammar"

# tokens/colors.css and tokens/semantic.css, verbatim.
DESIGN_TOKENS = {
    "canvas": "#07090D",
    "surface": "#1A1D24",
    "raised": "#23262F",
    "text": "#F5F7FA",
    "body": "#C5C7CE",
    "muted": "#8A8D96",
    "accent": "#3F6EE9",
    "accent_hover": "#5B84EE",
    "accent_press": "#3259C4",
    "on_accent": "#F5F7FA",
    "good": "#3FA46A",
    "warn": "#C98A2E",
    "danger": "#D8574F",
}


def read(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def read_code(name: str) -> str:
    """The file with its line comments removed, so prose about a banned pattern
    does not read as the pattern itself."""
    return "\n".join(re.sub(r"//.*$", "", line) for line in read(name).splitlines())


# --------------------------------------------------------------- typeface ---
def test_inter_ships_with_the_package():
    for weight in ("Inter-Regular.woff2", "Inter-SemiBold.woff2"):
        assert (default_font_dir() / weight).is_file(), f"{weight} must ship with the compiler"


def test_font_faces_are_embedded_not_linked():
    css = inline_font_face_css()
    assert css.count("@font-face") == 2, "exactly two weights: 400 and 600"
    assert "font-weight:400" in css and "font-weight:600" in css
    assert "data:font/woff2;base64," in css, "fonts are embedded, so a render box needs no network"
    assert "http" not in css, "no remote font request may enter a rendered frame"


def test_preview_template_embeds_the_font_and_waits_for_it():
    player = read("player.html.j2")
    assert "{{ font_face_css }}" in player, "the preview must carry the embedded faces"
    assert "document.fonts" in player, "the first exported frame must not race the font load"
    assert "LAKA_READY" in player
    ready = player[player.index("fontsReady") :]
    assert "window.LAKA_READY=true" in ready, "readiness is signalled after fonts resolve"


def test_only_two_font_weights_are_used():
    combined = read("player.html.j2") + read("studio-renderer.js")
    weights = set(re.findall(r"font:\s*(\d{3})\s", combined))
    assert weights <= {"400", "600"}, f"design system allows 400 and 600 only, found {sorted(weights)}"


# ----------------------------------------------------------------- colour ---
def test_brand_preset_matches_the_design_tokens():
    for grammar_dir in (GRAMMAR_SOURCE, GRAMMAR_PACKAGED):
        brand = yaml.safe_load((grammar_dir / "brand.example.yml").read_text(encoding="utf-8"))
        colors = brand["colors"]
        for key, expected in DESIGN_TOKENS.items():
            assert colors[key] == expected, f"{grammar_dir.name}/brand.example.yml {key} drifted from the token"


def test_brand_preset_uses_only_the_two_shipped_weights():
    brand = yaml.safe_load((GRAMMAR_SOURCE / "brand.example.yml").read_text(encoding="utf-8"))
    assert brand["type"]["weight_head"] == 600
    assert brand["type"]["weight_body"] == 400


def test_source_and_packaged_grammar_agree():
    """Walks subdirectories: grammar/lexicon/ is a whole tree that can drift."""
    for path in sorted(GRAMMAR_SOURCE.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(GRAMMAR_SOURCE)
        mirrored = GRAMMAR_PACKAGED / relative
        assert mirrored.is_file(), f"{relative} is missing from the packaged grammar"
        assert mirrored.read_bytes() == path.read_bytes(), f"{relative} differs between grammar/ and the package"


# ----------------------------------------------------------------- motion ---
def test_nothing_bounces():
    renderer = read_code("studio-renderer.js")
    assert "easeBack" not in renderer, "the design system has no overshoot; nothing snaps or bounces"
    assert "dsEase" in renderer, "one curve: cubic-bezier(0.16, 1, 0.3, 1)"
    assert "0.16" in renderer and "0.3" in renderer


def test_no_decorative_particle_field_or_blinking():
    renderer = read_code("studio-renderer.js")
    for banned in ("dotField", "blink", "Math.abs(Math.sin"):
        assert banned not in renderer, f"{banned} is not part of the visual system"


def test_scene_content_does_not_repaint_the_frame_chrome():
    """renderAt owns the canvas, backlight, grain and dolly — exactly once."""
    player = read("player.html.j2")
    frame = player[player.index("stage.innerHTML=`<div") : player.index("if (DEBUG)")]
    assert frame.count("background:${BACKLIGHT}") == 1
    assert frame.count("${drift}") == 1
    renderer = read_code("studio-renderer.js")
    assert "inset:-2%" not in renderer, "a second inset layer shifts every scene off its own left rail"


# ------------------------------------------------------------------- text ---
@pytest.mark.parametrize(
    ("spoken", "expected"),
    [
        ("Ryan Perez dot c a is where it comes together.", "ryanperez.ca is where it comes together."),
        ("Visit bow tie kreative dot com today", "Visit bowtiekreative.com today"),
        ("Go to all inclusive websites dot com", "Go to allinclusivewebsites.com"),
        ("hustlezone dot org and more", "hustlezone.org and more"),
        ("She connected the dot to the line", "She connected the dot to the line"),
    ],
)
def test_spoken_addresses_become_written_ones(spoken, expected):
    assert normalize_spoken_domains(spoken) == expected


def test_transcript_ingest_normalizes_addresses(tmp_path):
    from laka_video.srt import parse_srt

    srt = tmp_path / "sample.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:04,000\nRyan Perez dot c a is where it comes together.\n",
        encoding="utf-8",
    )
    assert parse_srt(srt)[0].text.startswith("ryanperez.ca is where")


@pytest.mark.parametrize(
    "sentence",
    [
        "You might know me through Bow Tie Kreative, my podcast, or something I have built",
        "We start with what is happening, look at who it affects, and work toward a step",
        "A place can look welcoming in a photograph and feel completely different in person",
    ],
)
def test_headlines_never_end_on_a_function_word(sentence):
    from laka_video.text_rules import _headline_span

    headline = _headline_span(sentence, set())
    last = re.sub(r"[^\w'’-]", "", headline.split()[-1].lower())
    banned = {"at", "who", "the", "a", "and", "to", "of", "in", "with", "for", "my", "or", "is"}
    assert last not in banned, f"headline stopped on a function word: {headline!r}"
    assert not headline.endswith("…"), "headlines are fitted by the renderer, never truncated with an ellipsis"


def test_headline_keeps_the_sentence_subject():
    from laka_video.text_rules import _headline_span

    stopwords = {"you", "a", "the", "i", "we"}
    headline = _headline_span(
        "You might know me through Bow Tie Kreative, my podcast, or something I have built", stopwords
    )
    assert headline.startswith("You "), "dropping the subject to save a word breaks the grammar"


def test_domains_keep_their_own_casing():
    from laka_video.text_rules import _clean_fragment

    assert _clean_fragment("ryanperez.ca is where it comes together") == "ryanperez.ca is where it comes together"
    assert _clean_fragment("hello there").startswith("Hello")


# -------------------------------------------------------------- packaging ---
def test_every_runtime_asset_is_declared_as_package_data():
    """A file under data/ that no glob matches is missing from the wheel.

    This is how the design system disappears in production without anything
    failing: the fonts are simply absent, inline_font_face_css() returns an
    empty string, and every frame renders in whatever the base image has.
    """
    import fnmatch
    import tomllib

    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    globs = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    patterns = globs["tool"]["setuptools"]["package-data"]["laka_video"]

    data_root = PACKAGE / "data"
    missing = []
    for path in sorted(data_root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(PACKAGE).as_posix()
        if not any(fnmatch.fnmatch(relative, pattern) for pattern in patterns):
            missing.append(relative)
    assert not missing, f"not shipped in the wheel: {missing}"


# ------------------------------------------------- perception in the render ---
def test_no_type_falls_below_the_legibility_floor():
    """Body-grade minimums are clamped to the published floor, not to a literal.

    Seven `min:` clamps sat at 2.2-2.6U against a 2.8U floor, which is 22-26px
    on a 1080 short edge where the floor is 28px.
    """
    import yaml

    floor = float(
        yaml.safe_load((GRAMMAR_SOURCE / "perception.yml").read_text(encoding="utf-8"))
        ["typography"]["body_min_units"]
    )
    renderer = read_code("studio-renderer.js")
    literals = [float(v) for v in re.findall(r"\bmin:\s*([\d.]+)\b", renderer)]
    below = [v for v in literals if v < floor]
    assert not below, f"minimums below the {floor}U legibility floor: {below}"
    assert "BODY_FLOOR" in renderer
    assert "body_min_units" in renderer, "the floor must be read from perception.yml"


def test_aspect_drives_the_entrance():
    """Achievements cut, states hold, activities never fully settle."""
    renderer = read_code("studio-renderer.js")
    assert "sceneOperator" in renderer
    for operator in ('"cut"', '"static"', '"loop"'):
        assert operator in renderer, f"motion operator {operator} is not handled"


def test_stagger_adapts_to_item_count():
    """clamp(1200/n, 60, 120): the step shrinks so the total build stays bounded."""
    renderer = read_code("studio-renderer.js")
    assert "staggerFor" in renderer
    assert "STAGGER_BUDGET" in renderer and "STAGGER_BAND" in renderer
    assert "index * 90" not in renderer, "a fixed 90ms step ignores list length"


def test_a_strike_is_never_drawn_across_a_free_headline():
    """Without a parser the negated span is unknown, and striking a whole line
    for a phrase-level negation states the opposite of the sentence."""
    renderer = read_code("studio-renderer.js")
    block = renderer[renderer.index("function statementFrame"):renderer.index("function structuredFrame")]
    assert "strikeThrough(" not in block, "statement frames must not draw a strike"


def test_negation_markers_are_predicate_scoped():
    """'without knowing why' is a manner adjunct, not a negation of the claim."""
    import yaml

    doc = yaml.safe_load((GRAMMAR_SOURCE / "lexicon" / "negation.yml").read_text(encoding="utf-8"))
    flat = " ".join(str(v) for group in doc["markers"].values() for v in group)
    assert "without" not in flat, "'without' scopes over its complement, not the clause"
    assert "lack" not in flat, "privatives describe a state; they do not negate a predicate"


def test_the_composition_pass_owns_the_accent_bleed():
    renderer = read_code("studio-renderer.js")
    assert "scene.accent_bleed" in renderer, "the renderer must honour the composition pass"
