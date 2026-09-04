from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .utils import default_template_path


def render_preview(
    storyboard: dict[str, Any],
    output_path: str | Path,
    audio_src: str,
    music_src: str | None = None,
    template_path: str | Path | None = None,
) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    template_file = Path(template_path) if template_path else default_template_path()
    env = Environment(
        loader=FileSystemLoader(str(template_file.parent)),
        autoescape=select_autoescape(enabled_extensions=("html", "xml")),
    )
    template = env.get_template(template_file.name)
    studio_renderer_path = template_file.parent / "studio-renderer.js"
    studio_renderer_js = studio_renderer_path.read_text(encoding="utf-8") if studio_renderer_path.exists() else ""
    storyboard_json = json.dumps(storyboard, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = template.render(
        storyboard_json=storyboard_json,
        audio_src=audio_src,
        music_src=music_src or "",
        title=storyboard.get("project", {}).get("title", "LAVC Preview"),
        studio_renderer_js=studio_renderer_js,
    )
    target.write_text(html, encoding="utf-8")
    return target
