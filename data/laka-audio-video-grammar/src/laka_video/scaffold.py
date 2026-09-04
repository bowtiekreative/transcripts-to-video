from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

import yaml

from .utils import default_grammar_dir


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "laka-video-project"


def _copy(source: Path, destination: Path) -> None:
    if source.resolve() == destination.resolve():
        return
    shutil.copy2(source, destination)


def init_project(
    destination: str | Path,
    audio: str | Path | None = None,
    transcript: str | Path | None = None,
    title: str = "My LAKA Video",
    mode: str = "auto",
    aspect: str = "9:16",
    seed: int | str = 33,
    force: bool = False,
) -> dict[str, Path]:
    dest = Path(destination).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)
    protected = [dest / "project.yml", dest / "brand.yml"]
    if not force and any(path.exists() for path in protected):
        raise ValueError(f"Project already exists in {dest}; use --force to replace scaffold files.")

    audio_name = "audio.wav"
    if audio:
        audio_source = Path(audio).expanduser().resolve()
        if not audio_source.exists():
            raise FileNotFoundError(f"Audio not found: {audio_source}")
        audio_name = f"audio{audio_source.suffix.lower() or '.wav'}"
        _copy(audio_source, dest / audio_name)
    else:
        (dest / "PLACE_AUDIO_HERE.txt").write_text(
            "Place an audio file in this folder and update source.audio in project.yml.\n",
            encoding="utf-8",
        )

    transcript_name: str | None = None
    if transcript:
        transcript_source = Path(transcript).expanduser().resolve()
        if not transcript_source.exists():
            raise FileNotFoundError(f"Transcript not found: {transcript_source}")
        transcript_name = "subtitles.srt"
        _copy(transcript_source, dest / transcript_name)

    resolved_mode = mode
    if mode == "auto":
        resolved_mode = "transcript" if transcript_name else "audio"
    if resolved_mode in {"transcript", "directed"} and not transcript_name:
        transcript_name = "subtitles.srt"
        (dest / transcript_name).write_text(
            "1\n00:00:00,000 --> 00:00:05,000\n"
            "[[LAKA relation=identity headline=\"Replace this cue\"]]\n"
            "Replace this line with words spoken during the first five seconds.\n",
            encoding="utf-8",
        )

    grammar = default_grammar_dir()
    _copy(grammar / "brand.example.yml", dest / "brand.yml")
    (dest / "overrides.yml").write_text(
        "# Optional deterministic overrides. Match by scene, cue, time, or exact text.\n"
        "overrides: []\n"
        "# Example:\n"
        "# - cue: 2\n"
        "#   relation: transformation\n"
        "#   infographic: transformation_arrow\n"
        "#   left: Attention\n"
        "#   right: Action\n",
        encoding="utf-8",
    )
    (dest / "data.yml").write_text(
        "# Explicit data is required for charts and matrices.\n"
        "data: {}\n"
        "# Example:\n"
        "#   campaign_results:\n"
        "#     series:\n"
        "#       - {label: Baseline, value: 12}\n"
        "#       - {label: Variant, value: 19}\n"
        "#     unit: conversions\n",
        encoding="utf-8",
    )

    project: dict[str, Any] = {
        "project": {"id": _slug(title), "title": title, "seed": seed},
        "source": {
            "audio": audio_name,
            "transcript": transcript_name,
            "mode": resolved_mode,
            "music": None,
            "overrides": "overrides.yml",
            "data": "data.yml",
        },
        "content": {"speaker": "", "destination": ""},
        "brand": {"preset": "brand.yml"},
        "output": {
            "directory": "build",
            "aspect": aspect,
            "fps": 30,
            "tail_seconds": 2.0,
            "captions": "karaoke" if transcript_name else "none",
            "copy_media": True,
        },
        "rules": {
            "min_scene_seconds": 3.5,
            "target_scene_seconds": 7.5,
            "max_scene_seconds": 12.0,
        },
    }
    project_path = dest / "project.yml"
    project_path.write_text(yaml.safe_dump(project, sort_keys=False, allow_unicode=True), encoding="utf-8")
    (dest / "README.txt").write_text(
        "Compile: laka-video compile project.yml\n"
        "Preview: open build/preview.html\n"
        "Explain: laka-video explain build/storyboard.json\n"
        "Render: laka-video render project.yml --quality draft\n",
        encoding="utf-8",
    )
    return {
        "directory": dest,
        "project": project_path,
        "brand": dest / "brand.yml",
        "overrides": dest / "overrides.yml",
        "data": dest / "data.yml",
    }
