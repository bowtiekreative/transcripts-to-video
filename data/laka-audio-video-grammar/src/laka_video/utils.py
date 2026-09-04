from __future__ import annotations

import base64
import copy
import hashlib
import json
import math
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml


def package_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_grammar_dir() -> Path:
    env = os.environ.get("LAVC_GRAMMAR_DIR")
    if env:
        return Path(env).expanduser().resolve()
    repo_candidate = package_root() / "grammar"
    if repo_candidate.exists():
        return repo_candidate
    return Path(__file__).resolve().parent / "data" / "grammar"


def default_template_path() -> Path:
    packaged = Path(__file__).resolve().parent / "data" / "templates" / "player.html.j2"
    if packaged.exists():
        return packaged
    repo_candidate = package_root() / "templates" / "player.html.j2"
    if repo_candidate.exists():
        return repo_candidate
    return packaged


def load_yaml(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def resolve_path(base_dir: Path, value: str | None) -> Path | None:
    if not value:
        return None
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = base_dir / p
    return p.resolve()


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def words(text: str) -> list[str]:
    return re.findall(r"[\w’'-]+", text or "", flags=re.UNICODE)


def word_count(text: str) -> int:
    return len(words(text))


def stable_hash(*parts: Any) -> str:
    raw = "|".join(str(p) for p in parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def triangular_fit(value: float, low: float, high: float) -> float:
    if high <= low:
        return 1.0
    center = (low + high) / 2.0
    half = (high - low) / 2.0
    if low <= value <= high:
        return 1.0 - 0.22 * abs(value - center) / max(half, 1e-9)
    distance = low - value if value < low else value - high
    return max(0.0, 0.78 - distance / max(high - low, 1e-9))


def ffprobe_duration(path: str | Path) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()
        return float(out)
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as exc:
        raise RuntimeError(f"Could not measure audio duration for {path}: {exc}") from exc


def parse_scalar(value: str) -> Any:
    lower = value.lower()
    if lower in {"true", "yes", "on"}:
        return True
    if lower in {"false", "no", "off"}:
        return False
    if lower in {"null", "none"}:
        return None
    if "|" in value:
        return [parse_scalar(v.strip()) for v in value.split("|") if v.strip()]
    try:
        if re.fullmatch(r"-?\d+", value):
            return int(value)
        if re.fullmatch(r"-?\d*\.\d+", value):
            return float(value)
    except ValueError:
        pass
    return value


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items() if not str(k).startswith("_")}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return 0.0
    return value


def default_font_dir() -> Path:
    packaged = Path(__file__).resolve().parent / "data" / "fonts"
    if packaged.exists():
        return packaged
    return package_root() / "fonts"


def inline_font_face_css() -> str:
    """Base64 @font-face rules for Inter 400/600.

    The design system specifies Inter and nothing else. Referencing it by family
    name only is not enough: a headless render box usually has no Inter installed,
    so every frame silently falls back to a system face and the brand disappears.
    Embedding the two licensed weights keeps rendering deterministic and offline.
    """
    font_dir = default_font_dir()
    faces = [("Inter-Regular.woff2", 400), ("Inter-SemiBold.woff2", 600)]
    rules: list[str] = []
    for filename, weight in faces:
        path = font_dir / filename
        if not path.exists():
            continue
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        rules.append(
            "@font-face{font-family:'Inter';font-style:normal;font-weight:%d;font-display:block;"
            "src:url(data:font/woff2;base64,%s) format('woff2');}" % (weight, encoded)
        )
    return "\n".join(rules)


# Dictated transcripts spell domains out loud: "ryan perez dot c a", "bow tie
# kreative dot com". Left alone they become headlines like "Ryan Perez dot c a
# is where", which is both ugly and factually not the address. Folding them back
# into a real domain is deterministic and reversible by inspection.
_TLD_SPELLINGS: dict[str, str] = {
    "com": "com", "c o m": "com",
    "ca": "ca", "c a": "ca",
    "net": "net", "n e t": "net",
    "org": "org", "o r g": "org",
    "io": "io", "i o": "io",
    "co": "co", "c o": "co",
    "dev": "dev", "app": "app", "ai": "ai", "a i": "ai",
}

_DOMAIN_LEAD_IN = {
    "visit", "go", "goto", "at", "to", "on", "see", "check", "head", "find", "the", "a", "an",
    "my", "our", "your", "is", "its", "it", "and", "or", "but", "so", "from", "via", "over",
}

_SPOKEN_DOMAIN_RE = re.compile(
    r"\b(?P<name>(?:[A-Za-z][\w'’-]*)(?:\s+[A-Za-z][\w'’-]*){0,3})"
    r"\s+dot\s+"
    r"(?P<tld>c\s*o\s*m|c\s*a|n\s*e\s*t|o\s*r\s*g|i\s*o|c\s*o|d\s*e\s*v|a\s*p\s*p|a\s*i)"
    r"(?![\w'’-])",
    flags=re.IGNORECASE,
)


def normalize_spoken_domains(text: str) -> str:
    """Fold spoken web addresses back into written ones.

    "Ryan Perez dot c a" -> "ryanperez.ca". Only the name words immediately in
    front of "dot" are folded, and only when the trailing token is a real TLD
    spelling, so ordinary prose containing the word "dot" is left alone.
    """
    def replace(match: re.Match[str]) -> str:
        tld = _TLD_SPELLINGS.get(re.sub(r"\s+", " ", match.group("tld").lower()).strip())
        if not tld:
            return match.group(0)
        # Only the name words belong in the domain. "Visit bow tie kreative dot
        # com" is bowtiekreative.com, not visitbowtiekreative.com.
        tokens = match.group("name").split()
        while tokens and re.sub(r"[^\w]", "", tokens[0].lower()) in _DOMAIN_LEAD_IN:
            tokens.pop(0)
        if not tokens:
            return match.group(0)
        prefix = match.group("name")[: match.group("name").rfind(tokens[0])] if len(tokens) < len(match.group("name").split()) else ""
        name = re.sub(r"['’]", "", " ".join(tokens))
        name = re.sub(r"[^\w-]+", "", name).lower()
        if not name:
            return match.group(0)
        return f"{prefix}{name}.{tld}"

    return _SPOKEN_DOMAIN_RE.sub(replace, text or "")


# Motion primitives the design system does not have. The Studio library was
# authored before the audit, so 30 of its elements overshoot, 8 rotate and 13
# reach for a colour that is not a token. Conforming them at load time keeps the
# author's file as the source of truth while the rendered frame still obeys the
# system — rather than forking the library and letting the two drift.
_OVERSHOOT_EASE = re.compile(
    r"const eb=p=>\{p=clamp\(p\);const c1=1\.70158,c3=c1\+1;"
    r"return 1\+c3\*Math\.pow\(p-1,3\)\+c1\*Math\.pow\(p-1,2\);\};"
)
_ROTATE_CALL = re.compile(r"\s*rotate\(\$\{[^}]*\}deg\)")
_ROTATE_LITERAL = re.compile(r"\s*rotate\([^)]*deg\)")


def conform_elements_js(source: str) -> tuple[str, dict[str, int]]:
    """Bring the Studio element library into the design system.

    Three substitutions, each replacing something the system forbids:
      * the overshoot easing becomes the system's single ease-out curve
      * rotation is removed from transforms
      * accent2 is counted, and resolved at the context boundary by the renderer

    Returns the conformed source and a count of what changed, so the swap is
    auditable rather than silent.
    """
    counts = {"overshoot": 0, "rotation": 0, "off_token_colour": 0}

    source, counts["overshoot"] = _OVERSHOOT_EASE.subn(
        "const eb=p=>{p=clamp(p);const cx=3*0.16,bx=3*(0.3-0.16)-cx,ax=1-cx-bx;"
        "let u=p;for(let i=0;i<6;i++){const f=((ax*u+bx)*u+cx)*u-p;"
        "const d=(3*ax*u+2*bx)*u+cx;if(Math.abs(f)<1e-6||Math.abs(d)<1e-6)break;u-=f/d;}"
        "u=clamp(u);const cy=3,by=-3,ay=1;return ((ay*u+by)*u+cy)*u;};",
        source,
    )
    source, rotations = _ROTATE_CALL.subn("", source)
    source, literal_rotations = _ROTATE_LITERAL.subn("", source)
    counts["rotation"] = rotations + literal_rotations
    # Colour is NOT rewritten. The library reads every colour from the context
    # object the renderer hands it, so the off-token name is resolved there by
    # binding accent2 to the accent-hover token. Rewriting call sites turned
    # `x.c.accent2` into `x.(c.accentHover||...)` and broke the parse — and it
    # was the wrong place regardless, since the boundary already exists.
    counts["off_token_colour"] = source.count("c.accent2")
    return source, counts


def studio_elements_js() -> tuple[str, dict[str, int]]:
    path = Path(__file__).resolve().parent / "data" / "templates" / "lavc-elements.js"
    if not path.exists():
        return "", {}
    return conform_elements_js(path.read_text(encoding="utf-8"))
