"""Accessibility as a hard gate, not an afterthought (nd-ux; MOTION_MATH §7).

This compiler exists to put a neurodivergent speaker's own words on screen, so
"reduce cognitive load first" is the brief rather than a compliance checkbox.
Four things are enforced here that the rest of the pipeline could only measure:

  * contrast, computed from the brand palette actually in use
  * vestibular safety — travel, scale and flash rate
  * a reduced-motion cut that keeps every duration and drops every translation
  * reading level of the words that reach the frame

Nothing here guesses. Contrast is arithmetic on the hex values in the brand, and
the reduced-motion cut is the same storyboard with motion parameters rewritten,
so the two versions stay frame-for-frame in sync.
"""
from __future__ import annotations

import re
from typing import Any

# ------------------------------------------------------------------ colour ---
_HEX = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_RGBA = re.compile(r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)")


def parse_colour(value: str, over: tuple[float, float, float] | None = None) -> tuple[float, float, float] | None:
    """Return sRGB 0-255. A translucent colour is composited over `over` first,
    because a hairline at 8% alpha does not have the contrast of white."""
    text = str(value or "").strip()
    match = _HEX.match(text)
    if match:
        digits = match.group(1)
        if len(digits) == 3:
            digits = "".join(c * 2 for c in digits)
        return tuple(int(digits[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
    match = _RGBA.match(text)
    if match:
        red, green, blue = (float(match.group(i)) for i in (1, 2, 3))
        alpha = float(match.group(4)) if match.group(4) is not None else 1.0
        if alpha < 1.0 and over is not None:
            red = red * alpha + over[0] * (1 - alpha)
            green = green * alpha + over[1] * (1 - alpha)
            blue = blue * alpha + over[2] * (1 - alpha)
        return (red, green, blue)
    return None


def relative_luminance(rgb: tuple[float, float, float]) -> float:
    """WCAG 2.x relative luminance."""
    channels = []
    for value in rgb:
        c = value / 255.0
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground: str, background: str) -> float | None:
    back = parse_colour(background)
    if back is None:
        return None
    fore = parse_colour(foreground, over=back)
    if fore is None:
        return None
    light, dark = sorted((relative_luminance(fore), relative_luminance(back)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


# The pairs the renderer actually draws. Checking the palette in the abstract
# would pass colours that never touch each other and miss the ones that do.
DRAWN_PAIRS: list[tuple[str, str, str, str]] = [
    ("text", "canvas", "headline", "large"),
    ("body", "canvas", "body copy", "body"),
    ("muted", "canvas", "micro-label", "body"),
    ("text", "surface", "card headline", "large"),
    ("body", "surface", "card body", "body"),
    ("muted", "surface", "card label", "body"),
    ("text", "raised", "raised card headline", "large"),
    ("accent", "canvas", "accent mark", "large"),
    ("accent_hover", "canvas", "accent label", "body"),
    ("on_accent", "accent", "text on the accent frame", "large"),
    ("danger", "canvas", "warning mark", "large"),
]


def audit_contrast(brand: dict[str, Any], perception: dict[str, Any]) -> list[dict[str, Any]]:
    """Every foreground/background pair the renderer puts on screen."""
    colours = (brand or {}).get("colors", {}) or {}
    typography = (perception or {}).get("typography", {}) or {}
    body_min = float(typography.get("contrast_body", 4.5))
    large_min = float(typography.get("contrast_large", 3.0))

    findings: list[dict[str, Any]] = []
    for fore_key, back_key, label, size in DRAWN_PAIRS:
        fore, back = colours.get(fore_key), colours.get(back_key)
        if not fore or not back:
            continue
        ratio = contrast_ratio(str(fore), str(back))
        if ratio is None:
            continue
        required = large_min if size == "large" else body_min
        findings.append({
            "pair": f"{fore_key} on {back_key}",
            "label": label,
            "ratio": round(ratio, 2),
            "required": required,
            "passes": ratio >= required,
        })
    return findings


# -------------------------------------------------------------- vestibular ---
def audit_motion(storyboard: dict[str, Any], perception: dict[str, Any]) -> list[dict[str, Any]]:
    """Travel, scale and flash rate against the vestibular risk factors."""
    access = (perception or {}).get("accessibility", {}) or {}
    max_scale = float(access.get("max_scale_change", 1.3))
    max_rate = float((perception.get("motion", {}) or {}).get("camera_scale_rate_per_second_max", 0.02))
    max_flash = float(access.get("max_flashes_per_second", 3))

    findings: list[dict[str, Any]] = []
    for scene in storyboard.get("scenes", []) or []:
        duration = max(0.01, float(scene.get("end", 0)) - float(scene.get("start", 0)))
        parameters = (scene.get("motion", {}) or {}).get("parameters", {}) or {}
        if parameters.get("camera_drift"):
            energy = float(parameters.get("energy", 0.5))
            total = 0.008 + 0.012 * energy
            findings.append({
                "scene_id": scene.get("id"),
                "check": "camera_scale_rate",
                "value": round(total / duration, 5),
                "limit": max_rate,
                "passes": (total / duration) <= max_rate,
            })
            findings.append({
                "scene_id": scene.get("id"),
                "check": "total_scale_change",
                "value": round(1 + total, 4),
                "limit": max_scale,
                "passes": (1 + total) <= max_scale,
            })
        # A cut is not a flash, but a run of very short scenes is a flicker.
        if duration < 1.0 / max_flash:
            findings.append({
                "scene_id": scene.get("id"),
                "check": "flash_rate",
                "value": round(1.0 / duration, 2),
                "limit": max_flash,
                "passes": False,
            })
    return findings


# ---------------------------------------------------------- reduced motion ---
def apply_reduced_motion(storyboard: dict[str, Any]) -> dict[str, Any]:
    """Rewrite a storyboard so every translation becomes an opacity change.

    WCAG 2.3.3 and the nd-ux brief: keep the duration, drop the travel. The cut
    stays frame-for-frame identical to the standard one — same scenes, same
    boundaries, same words — so the two versions can be published as the same
    film rather than as two different edits. Only the movement is removed.
    """
    storyboard = dict(storyboard)
    composition = dict(storyboard.get("composition", {}) or {})
    composition["reduced_motion"] = True
    storyboard["composition"] = composition

    scenes = []
    for scene in storyboard.get("scenes", []) or []:
        scene = dict(scene)
        motion = dict(scene.get("motion", {}) or {})
        parameters = dict(motion.get("parameters", {}) or {})
        parameters["camera_drift"] = False
        parameters["travel_px"] = 0
        parameters["parallax"] = False
        parameters["reduced_motion"] = True
        motion["parameters"] = parameters
        scene["motion"] = motion
        # An activity's residual drift is motion by definition; a reduced cut
        # holds it instead, which keeps the aspect reading without the movement.
        semantics = dict(scene.get("semantics", {}) or {})
        if semantics.get("motion_operator") == "loop":
            semantics["motion_operator"] = "static"
            semantics["motion_operator_reduced_from"] = "loop"
        scene["semantics"] = semantics
        scenes.append(scene)
    storyboard["scenes"] = scenes
    return storyboard


# -------------------------------------------------------------- readability ---
_VOWELS = re.compile(r"[aeiouy]+", re.IGNORECASE)


def syllables(word: str) -> int:
    """Rough syllable count. Good enough for a grade-level band, and stable."""
    token = re.sub(r"[^a-z]", "", word.lower())
    if not token:
        return 0
    groups = _VOWELS.findall(token)
    count = len(groups)
    if token.endswith("e") and count > 1 and not token.endswith(("le", "ee", "ye")):
        count -= 1
    return max(1, count)


# Flesch-Kincaid assumes running prose. Applied to a four-word label it reports
# nonsense — "Difficult experiences -> Constructive action" scores grade 21
# because the formula reads four polysyllabic words as one enormous sentence.
# A headline is not prose, so it gets the measure that actually applies to it.
PROSE_MIN_WORDS = 8


def lexical_density(text: str) -> float | None:
    """Mean syllables per word: the part of reading difficulty a label can have.

    A short label has no sentence structure to measure, but it can still be
    built from words most people have to decode rather than recognise.
    """
    tokens = re.findall(r"[A-Za-z][A-Za-z'-]*", str(text or ""))
    if not tokens:
        return None
    return sum(syllables(t) for t in tokens) / len(tokens)


def reading_difficulty(text: str) -> tuple[str, float] | None:
    """Return (measure, value) using the instrument that fits the text length."""
    tokens = re.findall(r"[A-Za-z][A-Za-z'-]*", str(text or ""))
    if not tokens:
        return None
    if len(tokens) >= PROSE_MIN_WORDS:
        grade = flesch_kincaid_grade(text)
        return ("grade", grade) if grade is not None else None
    density = lexical_density(text)
    return ("syllables_per_word", density) if density is not None else None


def flesch_kincaid_grade(text: str) -> float | None:
    """US grade level. nd-ux targets grade 6-8 for plain language.

    Only meaningful on running prose of at least PROSE_MIN_WORDS; use
    reading_difficulty() to pick the right instrument automatically.
    """
    sentences = [s for s in re.split(r"[.!?]+", str(text or "")) if s.strip()]
    tokens = re.findall(r"[A-Za-z][A-Za-z'-]*", str(text or ""))
    if not tokens or not sentences:
        return None
    total_syllables = sum(syllables(t) for t in tokens)
    words_per_sentence = len(tokens) / len(sentences)
    syllables_per_word = total_syllables / len(tokens)
    return 0.39 * words_per_sentence + 11.8 * syllables_per_word - 15.59
