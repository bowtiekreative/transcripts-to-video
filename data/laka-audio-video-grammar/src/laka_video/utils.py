from __future__ import annotations

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
    repo_candidate = package_root() / "templates" / "player.html.j2"
    if repo_candidate.exists():
        return repo_candidate
    return Path(__file__).resolve().parent / "data" / "templates" / "player.html.j2"


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
