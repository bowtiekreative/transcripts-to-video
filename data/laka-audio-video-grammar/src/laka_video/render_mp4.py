from __future__ import annotations

import base64
import json
import math
import mimetypes
import shutil
import subprocess
from pathlib import Path
from typing import Callable

from playwright.sync_api import sync_playwright


def _find_media(output_dir: Path, stem: str) -> Path | None:
    assets = output_dir / "assets"
    if not assets.exists():
        return None
    matches = sorted(p for p in assets.iterdir() if p.is_file() and p.stem == stem)
    return matches[0] if matches else None


def _image_sources(story: dict, output_dir: Path) -> dict[str, str]:
    sources = sorted(
        {
            str(scene.get("asset") or scene.get("payload", {}).get("asset"))
            for scene in story.get("scenes", [])
            if scene.get("asset") or scene.get("payload", {}).get("asset")
        }
    )
    resolved: dict[str, str] = {}
    for source in sources:
        if source.startswith(("data:", "http://", "https://")):
            resolved[source] = source
            continue
        asset_path = Path(source).expanduser()
        if not asset_path.is_absolute():
            asset_path = output_dir / asset_path
        asset_path = asset_path.resolve()
        if not asset_path.is_file():
            raise FileNotFoundError(f"Required scene image asset was not found: {source}")
        mime_type = mimetypes.guess_type(asset_path.name)[0] or "application/octet-stream"
        if not mime_type.startswith("image/"):
            raise ValueError(f"Required scene asset is not a supported image: {source}")
        encoded = base64.b64encode(asset_path.read_bytes()).decode("ascii")
        resolved[source] = f"data:{mime_type};base64,{encoded}"
    return resolved


def render_mp4(
    preview_path: str | Path,
    storyboard_path: str | Path,
    output_path: str | Path | None = None,
    quality: str = "standard",
    progress: Callable[[int, int], None] | None = None,
) -> Path:
    preview = Path(preview_path).resolve()
    storyboard_file = Path(storyboard_path).resolve()
    if not preview.exists() or not storyboard_file.exists():
        raise FileNotFoundError("Preview HTML and storyboard JSON must exist before rendering.")
    story = json.loads(storyboard_file.read_text(encoding="utf-8"))
    image_sources = _image_sources(story, preview.parent)
    comp = story["composition"]
    width, height = int(comp["width"]), int(comp["height"])
    duration = float(comp["duration"])
    project_fps = float(comp.get("fps", 30))
    quality = quality.lower()
    if quality == "draft":
        fps = min(12.0, project_fps)
        scale = 1.0
        crf = 25
        preset = "veryfast"
    elif quality == "high":
        fps = project_fps
        scale = 1.0
        crf = 17
        preset = "slow"
    else:
        fps = project_fps
        scale = 1.0
        crf = 20
        preset = "medium"
    out_width = max(2, int(round(width * scale / 2) * 2))
    out_height = max(2, int(round(height * scale / 2) * 2))
    output = Path(output_path).resolve() if output_path else preview.parent / "video.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)

    audio = _find_media(preview.parent, "audio")
    music = _find_media(preview.parent, "music")
    if audio is None:
        original = story.get("source", {}).get("audio_original")
        if original:
            candidate = Path(str(original)).expanduser()
            audio = candidate.resolve() if candidate.is_absolute() else (storyboard_file.parent / candidate).resolve()
        else:
            audio = None
    if audio is None or not audio.exists():
        raise FileNotFoundError("Could not locate compiled or original narration audio.")

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg was not found on PATH.")
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "warning",
        "-f", "image2pipe", "-vcodec", "png", "-r", str(fps), "-i", "pipe:0",
        "-i", str(audio),
    ]
    if music and music.exists():
        cmd += ["-i", str(music)]
        cmd += [
            "-filter_complex",
            f"[0:v]scale={out_width}:{out_height}:flags=lanczos[v];"
            "[1:a]volume=1.0[a1];[2:a]volume=0.18[a2];"
            "[a1][a2]amix=inputs=2:duration=longest:dropout_transition=0,apad[a]",
            "-map", "[v]", "-map", "[a]",
        ]
    else:
        cmd += [
            "-filter_complex", f"[0:v]scale={out_width}:{out_height}:flags=lanczos[v];[1:a]apad[a]",
            "-map", "[v]", "-map", "[a]",
        ]
    cmd += [
        "-t", f"{duration:.6f}", "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(output),
    ]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert process.stdin is not None
    total_frames = int(math.ceil(duration * fps))

    chromium = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    with sync_playwright() as p:
        browser_type = p.chromium
        launch_kwargs = {
            "headless": True,
            "args": ["--allow-file-access-from-files", "--disable-gpu-sandbox", "--no-sandbox"],
        }
        if chromium:
            launch_kwargs["executable_path"] = chromium
        browser = browser_type.launch(**launch_kwargs)
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        # set_content avoids local-file navigation restrictions in sandboxed or managed Chromium.
        # A base URL keeps relative project assets resolvable during ordinary local rendering.
        html = preview.read_text(encoding="utf-8")
        html = html.replace("<head>", f'<head><base href="{preview.parent.as_uri()}/">', 1)
        for source, embedded in image_sources.items():
            html = html.replace(json.dumps(source), json.dumps(embedded))
        html = html.replace(
            'const EXPORT = new URLSearchParams(location.search).get("export") === "1";',
            'const EXPORT = true;',
            1,
        )
        page.set_content(html, wait_until="load")
        page.wait_for_function("window.LAKA_READY === true")
        if image_sources:
            failed_assets = page.evaluate(
                """async sources => {
                  const results = await Promise.all(sources.map(src => new Promise(resolve => {
                    const image = new Image();
                    image.onload = () => resolve(null);
                    image.onerror = () => resolve(src);
                    image.src = src;
                  })));
                  return results.filter(Boolean);
                }""",
                list(image_sources.values()),
            )
            if failed_assets:
                raise RuntimeError("Could not decode one or more required scene image assets.")
        stage = page.locator("#stage")
        try:
            for frame in range(total_frames):
                t = min(duration, frame / fps)
                page.evaluate("t => window.renderAt(t)", t)
                png = None
                last_error: Exception | None = None
                # A clipped page capture is substantially faster. If a managed Chromium build
                # rejects that protocol call, fall back to the exact stage locator.
                for attempt in range(2):
                    try:
                        png = page.screenshot(
                            type="png",
                            clip={"x": 0, "y": 0, "width": width, "height": height},
                            timeout=15000,
                        )
                        break
                    except Exception as exc:
                        last_error = exc
                        page.wait_for_timeout(50 * (attempt + 1))
                if png is None:
                    try:
                        png = stage.screenshot(type="png", timeout=20000)
                    except Exception as exc:
                        last_error = exc
                if png is None:
                    raise RuntimeError(f"Could not capture frame {frame}: {last_error}")
                process.stdin.write(png)
                if progress and (frame == 0 or frame + 1 == total_frames or frame % max(1, int(fps * 2)) == 0):
                    progress(frame + 1, total_frames)
        finally:
            try:
                process.stdin.close()
            except BrokenPipeError:
                pass
            browser.close()
    code = process.wait()
    if code != 0:
        raise RuntimeError(f"FFmpeg exited with status {code}.")
    return output
