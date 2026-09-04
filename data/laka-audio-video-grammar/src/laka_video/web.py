from __future__ import annotations

import copy
import json
import os
import secrets
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml
from flask import (
    Flask, abort, jsonify, redirect, render_template, request, send_file,
    send_from_directory, url_for,
)
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import RequestEntityTooLarge

from .compiler import compile_project
from .render_mp4 import render_mp4
from .scaffold import init_project
from .studio import allowed_review_choices, build_studio_review, load_studio_library
from .utils import default_font_dir


NARRATION_EXTENSIONS = {
    ".aac", ".flac", ".m4a", ".mkv", ".mov", ".mp3", ".mp4",
    ".oga", ".ogg", ".opus", ".wav", ".webm",
}
TRANSCRIPT_EXTENSIONS = {".srt"}
ASPECTS = {"9:16", "16:9", "1:1", "4:5"}
QUALITIES = {"draft", "standard", "high"}
COMPOSITION_MODES = {"studio", "wildcard"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


class UploadError(ValueError):
    """A correctable upload error that can be shown to the user."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_title(filename: str) -> str:
    words = Path(filename).stem.replace("_", " ").replace("-", " ").split()
    return " ".join(words).strip()[:80] or "Untitled recording"


def _lint_messages(report: dict[str, Any], severities: set[str]) -> list[str]:
    messages: list[str] = []
    for issue in report.get("issues", []):
        if issue.get("severity") not in severities:
            continue
        location = f"{issue['scene_id']}: " if issue.get("scene_id") else ""
        code = f"{issue['code']}: " if issue.get("code") else ""
        messages.append(f"{location}{code}{issue.get('message', 'Quality check issue')}")
    return messages


def _valid_image_header(upload: FileStorage, suffix: str) -> bool:
    position = upload.stream.tell()
    header = upload.stream.read(12)
    upload.stream.seek(position)
    if suffix == ".png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    if suffix in {".jpg", ".jpeg"}:
        return header.startswith(b"\xff\xd8\xff")
    if suffix == ".webp":
        return header.startswith(b"RIFF") and header[8:12] == b"WEBP"
    return False


class JobManager:
    def __init__(self, root: str | Path, max_workers: int = 1) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="laka-render")

    @staticmethod
    def _classify(files: Iterable[FileStorage]) -> tuple[FileStorage, FileStorage | None]:
        populated = [item for item in files if item and item.filename]
        unsupported = [item.filename for item in populated if Path(item.filename or "").suffix.lower() not in NARRATION_EXTENSIONS | TRANSCRIPT_EXTENSIONS]
        narration = [item for item in populated if Path(item.filename or "").suffix.lower() in NARRATION_EXTENSIONS]
        transcripts = [item for item in populated if Path(item.filename or "").suffix.lower() in TRANSCRIPT_EXTENSIONS]
        if unsupported:
            raise UploadError(f"Files: unsupported type for {unsupported[0]}. Add audio, video, or an SRT transcript.")
        if not narration:
            raise UploadError("Narration: add one audio or video file. An SRT alone has no soundtrack to render.")
        if len(narration) > 1:
            raise UploadError("Narration: add only one audio or video file per render.")
        if len(transcripts) > 1:
            raise UploadError("Transcript: add no more than one SRT file per render.")
        return narration[0], transcripts[0] if transcripts else None

    def create_job(
        self,
        files: Iterable[FileStorage],
        aspect: str = "16:9",
        quality: str = "standard",
        composition_mode: str = "wildcard",
    ) -> dict[str, Any]:
        narration, transcript = self._classify(files)
        if aspect not in ASPECTS:
            raise UploadError("Format: choose 9:16, 16:9, 1:1, or 4:5.")
        if quality not in QUALITIES:
            raise UploadError("Quality: choose draft, standard, or high.")
        if composition_mode not in COMPOSITION_MODES:
            raise UploadError("Composition: choose Studio review or Deterministic wildcard.")

        job_id = secrets.token_hex(6)
        job_dir = self.root / job_id
        upload_dir = job_dir / "uploads"
        project_dir = job_dir / "project"
        upload_dir.mkdir(parents=True)

        narration_suffix = Path(narration.filename or "").suffix.lower()
        narration_path = upload_dir / f"narration{narration_suffix}"
        narration.save(narration_path)
        transcript_path: Path | None = None
        if transcript:
            transcript_path = upload_dir / "subtitles.srt"
            transcript.save(transcript_path)

        job: dict[str, Any] = {
            "id": job_id,
            "status": "queued",
            "step": "Queued locally",
            "progress": 2,
            "message": "Your files are ready for the compiler.",
            "created_at": _now(),
            "updated_at": _now(),
            "narration_name": narration.filename,
            "transcript_name": transcript.filename if transcript else None,
            "aspect": aspect,
            "quality": quality,
            "composition_mode": composition_mode,
            "selection_seed": secrets.randbelow(2_147_483_647) if composition_mode == "wildcard" else 33,
            "mode": "transcript" if transcript else "audio",
            "error": None,
            "warnings": [],
            "review": None,
            "output": None,
            "_narration": narration_path,
            "_transcript": transcript_path,
            "_project_dir": project_dir,
        }
        with self._lock:
            self._jobs[job_id] = job
        return self.snapshot(job_id) or {}

    def start_job(self, job_id: str) -> None:
        if not self.snapshot(job_id):
            raise KeyError(job_id)
        self._executor.submit(self._run_job, job_id)

    def snapshot(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            return copy.deepcopy({key: value for key, value in job.items() if not key.startswith("_")})

    def _get_private(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._jobs[job_id])

    def _update(self, job_id: str, **changes: Any) -> None:
        with self._lock:
            self._jobs[job_id].update(changes, updated_at=_now())

    def _run_job(self, job_id: str) -> None:
        job = self._get_private(job_id)
        try:
            self._update(
                job_id,
                status="preparing",
                step="Reading input",
                progress=6,
                message="Measuring timing and preparing a local project.",
            )
            init_project(
                destination=job["_project_dir"],
                audio=job["_narration"],
                transcript=job["_transcript"],
                title=_safe_title(job["narration_name"]),
                mode=job["mode"],
                aspect=job["aspect"],
                seed=job["selection_seed"],
                composition_mode=job["composition_mode"],
            )

            self._update(
                job_id,
                status="compiling",
                step="Compiling structure",
                progress=14,
                message="Classifying meaning, selecting LAKA compositions, and building the EventMath timeline.",
            )
            paths, lint_status, warnings = self._compile(job_id, job["_project_dir"])
            if job["composition_mode"] == "studio":
                story = json.loads(paths["storyboard"].read_text(encoding="utf-8"))
                review = build_studio_review(story, load_studio_library())
                self._update(
                    job_id,
                    status="review",
                    step="Choose scene designs",
                    progress=28,
                    message=(
                        f"The Studio mapped {len(review['scenes'])} scenes. Choose a valid composition for each; "
                        "image scenes must have an image before rendering can start."
                    ),
                    warnings=warnings,
                    review=review,
                    _paths=paths,
                )
                return
            self._render(job_id, paths, lint_status, warnings)
        except Exception as exc:  # The worker must always publish a terminal state.
            self._fail(job_id, job, exc)

    def _compile(self, job_id: str, project_dir: Path) -> tuple[dict[str, Path], str, list[str]]:
        paths = compile_project(project_dir / "project.yml")
        lint = json.loads(paths["lint"].read_text(encoding="utf-8"))
        lint_status = str(lint.get("status") or "unknown")
        if lint_status not in {"pass", "warning"}:
            blocking = _lint_messages(lint, {"FATAL", "ERROR"})
            detail = "; ".join(blocking[:3]) or f"quality check returned {lint_status}"
            raise RuntimeError(f"Storyboard cannot render: {detail}.")
        warnings = _lint_messages(lint, {"WARNING"})
        self._update(job_id, warnings=warnings)
        return paths, lint_status, warnings

    def _render(
        self,
        job_id: str,
        paths: dict[str, Path],
        lint_status: str,
        warnings: list[str],
    ) -> None:
        self._update(
            job_id,
            status="rendering",
            step="Rendering video",
            progress=36,
            message="Drawing the approved Studio frames and encoding the MP4 locally.",
            review=None,
        )

        def on_progress(done: int, total: int) -> None:
            percent = 36 + int((done / max(total, 1)) * 60)
            self._update(job_id, progress=min(96, percent))

        job = self._get_private(job_id)
        output = render_mp4(
            paths["preview"],
            paths["storyboard"],
            quality=job["quality"],
            progress=on_progress,
        )
        story = json.loads(paths["storyboard"].read_text(encoding="utf-8"))
        composition = story["composition"]
        rendered_width = max(2, int(round(composition["width"] / 2) * 2))
        rendered_height = max(2, int(round(composition["height"] / 2) * 2))
        warning_count = len(warnings)
        completion_message = (
            f"Video finished with {warning_count} non-blocking quality note{'s' if warning_count != 1 else ''}. "
            "See the decision report for details."
            if warning_count
            else "The deterministic render passed its storyboard checks."
        )
        self._update(
            job_id,
            status="complete",
            step="Video ready",
            progress=100,
            message=completion_message,
            output={
                "filename": output.name,
                "duration": composition["duration"],
                "width": rendered_width,
                "height": rendered_height,
                "scenes": len(story["scenes"]),
                "size_bytes": output.stat().st_size,
                "lint_score": story["lint_summary"]["score"],
                "lint_status": lint_status,
                "warning_count": warning_count,
                "selection_mode": composition.get("selection_mode", "studio"),
                "selection_seed": story.get("studio", {}).get("seed"),
            },
            _video=output,
            _report=paths["decisions"],
        )

    def submit_review(
        self,
        job_id: str,
        selections: dict[str, str],
        assets: dict[str, FileStorage],
    ) -> None:
        job = self._get_private(job_id)
        if job.get("status") != "review" or not job.get("review"):
            raise UploadError("Studio review: this job is not waiting for scene choices.")
        allowed = allowed_review_choices(job["review"])
        plan: list[tuple[str, dict[str, Any], FileStorage | None]] = []
        for scene in job["review"].get("scenes", []):
            scene_id = str(scene["id"])
            selected_key = selections.get(scene_id) or str(scene["selected"])
            choice = allowed.get(scene_id, {}).get(selected_key)
            if choice is None:
                raise UploadError(f"Scene {scene['index']}: choose one of the Studio compositions shown.")
            asset = assets.get(scene_id)
            if choice.get("requires_asset"):
                if asset is None or not asset.filename:
                    raise UploadError(
                        f"Image for scene {scene['index']}: add a PNG, JPG, or WebP before starting the render."
                    )
                suffix = Path(asset.filename).suffix.lower()
                if suffix not in IMAGE_EXTENSIONS:
                    raise UploadError(
                        f"Image for scene {scene['index']}: {asset.filename} is not supported; add a PNG, JPG, or WebP."
                    )
                if not _valid_image_header(asset, suffix):
                    raise UploadError(
                        f"Image for scene {scene['index']}: {asset.filename} is not a valid {suffix.lstrip('.').upper()} image."
                    )
            plan.append((scene_id, choice, asset))

        build_assets = job["_project_dir"] / "build" / "assets"
        build_assets.mkdir(parents=True, exist_ok=True)
        overrides: list[dict[str, Any]] = []
        for scene_id, choice, asset in plan:
            item: dict[str, Any] = {
                "scene": scene_id,
                "infographic": choice["template"],
                "layout": choice["layout"],
            }
            if choice.get("requires_asset") and asset is not None:
                suffix = Path(asset.filename or "").suffix.lower()
                asset_name = f"{scene_id}{suffix}"
                asset.save(build_assets / asset_name)
                item.update(
                    {
                        "asset": f"assets/{asset_name}",
                        "asset_alt": f"Image supporting {scene_id}",
                        "asset_source": Path(asset.filename or asset_name).name,
                    }
                )
            overrides.append(item)

        (job["_project_dir"] / "overrides.yml").write_text(
            yaml.safe_dump({"overrides": overrides}, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        self._update(
            job_id,
            status="queued",
            step="Studio cut approved",
            progress=31,
            message="All selected image slots are filled. Recompiling the approved cut.",
            review=None,
        )
        self._executor.submit(self._resume_render, job_id)

    def _resume_render(self, job_id: str) -> None:
        job = self._get_private(job_id)
        try:
            self._update(
                job_id,
                status="compiling",
                step="Locking Studio choices",
                progress=33,
                message="Applying the approved scene designs and checking the final storyboard.",
            )
            paths, lint_status, warnings = self._compile(job_id, job["_project_dir"])
            self._render(job_id, paths, lint_status, warnings)
        except Exception as exc:
            self._fail(job_id, job, exc)

    def _fail(self, job_id: str, job: dict[str, Any], exc: Exception) -> None:
        project_dir = str(job["_project_dir"])
        message = str(exc).replace(project_dir, "project").strip() or exc.__class__.__name__
        self._update(
            job_id,
            status="failed",
            step="Render stopped",
            message="The compiler could not finish this file.",
            error=message[:500],
        )

    def artifact(self, job_id: str, key: str) -> Path | None:
        with self._lock:
            job = self._jobs.get(job_id)
            value = job.get(key) if job else None
            return Path(value) if value else None


def _serialize_job(job: dict[str, Any]) -> dict[str, Any]:
    result = dict(job)
    result["status_url"] = url_for("job_status", job_id=job["id"])
    if job["status"] == "review":
        result["render_url"] = url_for("job_render", job_id=job["id"])
    if job["status"] == "complete":
        result["video_url"] = url_for("job_video", job_id=job["id"])
        result["download_url"] = url_for("job_video", job_id=job["id"], download=1)
        result["report_url"] = url_for("job_report", job_id=job["id"])
    return result


def create_app(
    job_root: str | Path | None = None,
    manager: JobManager | None = None,
) -> Flask:
    asset_dir = Path(__file__).resolve().parent / "data" / "web"
    app = Flask(__name__, template_folder=str(asset_dir), static_folder=str(asset_dir), static_url_path="/assets")
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024

    # Inter is served from the package, not from a CDN: the compiler is meant to
    # run offline, and the console should not fall back to a system face when it
    # does.
    @app.route("/fonts/<path:filename>")
    def brand_font(filename: str):
        return send_from_directory(default_font_dir(), filename, max_age=31536000)
    configured_root = os.environ.get("LAVC_JOB_ROOT")
    resolved_root = Path(job_root) if job_root else Path(configured_root) if configured_root else Path.cwd() / ".laka" / "jobs"
    job_manager = manager or JobManager(resolved_root)
    app.extensions["lavc_job_manager"] = job_manager

    auth_username = os.environ.get("TRANSCRIBE_USERNAME")
    auth_password = os.environ.get("TRANSCRIBE_PASSWORD")
    if bool(auth_username) != bool(auth_password):
        raise RuntimeError("TRANSCRIBE_USERNAME and TRANSCRIBE_PASSWORD must be configured together.")

    @app.before_request
    def require_basic_auth() -> Any:
        if request.endpoint == "healthz" or not auth_username:
            return None
        supplied = request.authorization
        username_ok = secrets.compare_digest(supplied.username or "", auth_username) if supplied else False
        password_ok = secrets.compare_digest(supplied.password or "", auth_password or "") if supplied else False
        if username_ok and password_ok:
            return None
        return (
            jsonify({"error": "Authentication required."}),
            401,
            {"WWW-Authenticate": 'Basic realm="LAKA Transcribe"', "Cache-Control": "no-store"},
        )

    @app.after_request
    def no_store_api(response: Any) -> Any:
        if request.path.startswith("/api/") or request.path.startswith("/jobs"):
            response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.get("/healthz")
    def healthz() -> Any:
        return jsonify({"status": "ok"})

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(_: RequestEntityTooLarge) -> tuple[Any, int]:
        message = "Files: the combined upload is larger than 2 GB. Reduce the source size and try again."
        if request.accept_mimetypes.best == "application/json":
            return jsonify({"error": message}), 413
        return render_template("app.html.j2", initial_job=None, form_error=message), 413

    @app.get("/")
    def index() -> str:
        job_id = request.args.get("job", "")
        job = job_manager.snapshot(job_id) if job_id else None
        return render_template(
            "app.html.j2",
            initial_job=_serialize_job(job) if job else None,
            form_error=None,
        )

    @app.post("/jobs")
    def create_job() -> Any:
        try:
            job = job_manager.create_job(
                request.files.getlist("files"),
                aspect=request.form.get("aspect", "16:9"),
                quality=request.form.get("quality", "standard"),
                composition_mode=request.form.get("composition_mode", "wildcard"),
            )
        except UploadError as exc:
            if request.accept_mimetypes.best == "application/json":
                return jsonify({"error": str(exc)}), 400
            return render_template("app.html.j2", initial_job=None, form_error=str(exc)), 400
        job_manager.start_job(job["id"])
        if request.accept_mimetypes.best == "application/json":
            return jsonify(_serialize_job(job)), 202
        return redirect(url_for("index", job=job["id"]), code=303)

    @app.get("/api/jobs/<job_id>")
    def job_status(job_id: str) -> Any:
        job = job_manager.snapshot(job_id)
        if job is None:
            return jsonify({"error": "Render job not found."}), 404
        return jsonify(_serialize_job(job))

    @app.post("/jobs/<job_id>/render")
    def job_render(job_id: str) -> Any:
        job = job_manager.snapshot(job_id)
        if job is None:
            return jsonify({"error": "Render job not found."}), 404
        scene_ids = [str(scene.get("id")) for scene in (job.get("review") or {}).get("scenes", [])]
        selections = {scene_id: request.form.get(f"choice_{scene_id}", "") for scene_id in scene_ids}
        assets = {
            scene_id: request.files[f"asset_{scene_id}"]
            for scene_id in scene_ids
            if request.files.get(f"asset_{scene_id}")
        }
        try:
            job_manager.submit_review(job_id, selections, assets)
        except UploadError as exc:
            return jsonify({"error": str(exc)}), 400
        updated = job_manager.snapshot(job_id)
        return jsonify(_serialize_job(updated or job)), 202

    @app.get("/jobs/<job_id>/video")
    def job_video(job_id: str) -> Any:
        path = job_manager.artifact(job_id, "_video")
        if path is None or not path.is_file():
            abort(404)
        return send_file(
            path,
            mimetype="video/mp4",
            conditional=True,
            as_attachment=request.args.get("download") == "1",
            download_name="laka-video.mp4",
        )

    @app.get("/jobs/<job_id>/report")
    def job_report(job_id: str) -> Any:
        path = job_manager.artifact(job_id, "_report")
        if path is None or not path.is_file():
            abort(404)
        return send_file(path, mimetype="text/markdown", as_attachment=True, download_name="decision-report.md")

    return app


def run_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    job_root: str | Path | None = None,
    debug: bool = False,
) -> None:
    app = create_app(job_root=job_root)
    app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=debug)


def main() -> None:
    run_server()


if __name__ == "__main__":
    main()
