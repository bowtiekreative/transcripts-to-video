import base64
import io
import json
from pathlib import Path

import pytest
from werkzeug.datastructures import FileStorage

from laka_video.web import JobManager, UploadError, create_app


class QueuedManager(JobManager):
    def start_job(self, job_id: str) -> None:
        assert self.snapshot(job_id) is not None


def test_index_contains_accessible_intake_and_laka_header(tmp_path: Path):
    app = create_app(manager=QueuedManager(tmp_path))
    client = app.test_client()

    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert html.count("<h1") == 1
    assert 'for="files"' in html
    assert 'id="menu-button"' in html
    assert "btk-seal-white.png" in html
    assert "Powered by" in html
    assert 'value="studio" checked' in html
    assert 'value="wildcard"' in html
    assert 'id="studio-review"' in html


def test_srt_without_narration_returns_correctable_error(tmp_path: Path):
    app = create_app(manager=QueuedManager(tmp_path))
    client = app.test_client()

    response = client.post(
        "/jobs",
        data={"files": (io.BytesIO(b"1\n00:00:00,000 --> 00:00:01,000\nHello\n"), "words.srt")},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 400
    assert response.json["error"].startswith("Narration:")


def test_audio_upload_creates_a_queued_local_job(tmp_path: Path):
    manager = QueuedManager(tmp_path)
    app = create_app(manager=manager)
    client = app.test_client()

    response = client.post(
        "/jobs",
        data={
            "files": (io.BytesIO(b"not decoded during this test"), "voice.wav"),
            "aspect": "1:1",
            "quality": "draft",
        },
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 202
    assert response.json["status"] == "queued"
    assert response.json["aspect"] == "1:1"
    assert response.json["mode"] == "audio"
    job = manager.snapshot(response.json["id"])
    assert job is not None
    assert job["narration_name"] == "voice.wav"


def test_studio_upload_records_review_mode(tmp_path: Path):
    manager = QueuedManager(tmp_path)
    response = create_app(manager=manager).test_client().post(
        "/jobs",
        data={
            "files": (io.BytesIO(b"audio fixture"), "voice.wav"),
            "composition_mode": "studio",
        },
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 202
    assert response.json["composition_mode"] == "studio"
    assert response.json["selection_seed"] == 33


def test_selected_image_scene_cannot_render_without_an_image(tmp_path: Path):
    manager = QueuedManager(tmp_path)
    job = manager.create_job([FileFixture("voice.wav")], composition_mode="studio")
    manager._update(
        job["id"],
        status="review",
        review={
            "scenes": [
                {
                    "id": "scene-001",
                    "index": 1,
                    "selected": "title_card::vertical_rail",
                    "choices": [
                        {
                            "key": "title_card::vertical_rail",
                            "template": "title_card",
                            "layout": "vertical_rail",
                            "requires_asset": False,
                        },
                        {
                            "key": "title_card::image_overlay",
                            "template": "title_card",
                            "layout": "image_overlay",
                            "requires_asset": True,
                        },
                    ],
                }
            ]
        },
    )

    with pytest.raises(UploadError, match="Image for scene 1"):
        manager.submit_review(job["id"], {"scene-001": "title_card::image_overlay"}, {})


def test_selected_image_scene_rejects_a_fake_image_file(tmp_path: Path):
    manager = QueuedManager(tmp_path)
    job = manager.create_job([FileFixture("voice.wav")], composition_mode="studio")
    manager._update(
        job["id"],
        status="review",
        review={
            "scenes": [
                {
                    "id": "scene-001",
                    "index": 1,
                    "selected": "title_card::image_overlay",
                    "choices": [
                        {
                            "key": "title_card::image_overlay",
                            "template": "title_card",
                            "layout": "image_overlay",
                            "requires_asset": True,
                        }
                    ],
                }
            ]
        },
    )
    fake = FileStorage(stream=io.BytesIO(b"not really an image"), filename="visual.png")

    with pytest.raises(UploadError, match="not a valid PNG"):
        manager.submit_review(
            job["id"],
            {"scene-001": "title_card::image_overlay"},
            {"scene-001": fake},
        )


class FileFixture:
    def __init__(self, filename: str):
        self.filename = filename

    def save(self, path: Path) -> None:
        Path(path).write_bytes(b"fixture")


def test_default_upload_uses_full_film_format(tmp_path: Path):
    manager = QueuedManager(tmp_path)
    app = create_app(manager=manager)

    response = app.test_client().post(
        "/jobs",
        data={"files": (io.BytesIO(b"audio fixture"), "voice.wav")},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 202
    assert response.json["aspect"] == "16:9"
    assert response.json["quality"] == "standard"


def test_health_check_bypasses_configured_authentication(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TRANSCRIBE_USERNAME", "operator")
    monkeypatch.setenv("TRANSCRIBE_PASSWORD", "secret")
    app = create_app(manager=QueuedManager(tmp_path))

    response = app.test_client().get("/healthz")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_configured_authentication_protects_the_application(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TRANSCRIBE_USERNAME", "operator")
    monkeypatch.setenv("TRANSCRIBE_PASSWORD", "secret")
    app = create_app(manager=QueuedManager(tmp_path))
    client = app.test_client()

    denied = client.get("/")
    token = base64.b64encode(b"operator:secret").decode("ascii")
    allowed = client.get("/", headers={"Authorization": f"Basic {token}"})

    assert denied.status_code == 401
    assert denied.headers["WWW-Authenticate"] == 'Basic realm="LAKA Transcribe"'
    assert allowed.status_code == 200


def test_warning_quality_check_still_produces_video(tmp_path: Path, monkeypatch):
    compiled = tmp_path / "compiled"
    compiled.mkdir()
    storyboard = compiled / "storyboard.json"
    lint = compiled / "lint-report.json"
    preview = compiled / "preview.html"
    decisions = compiled / "decision-report.md"
    video = compiled / "video.mp4"
    storyboard.write_text(
        json.dumps(
            {
                "composition": {"duration": 8.0, "width": 1920, "height": 1080},
                "scenes": [{"id": "scene-001"}],
                "lint_summary": {"score": 97.5},
            }
        ),
        encoding="utf-8",
    )
    lint.write_text(
        json.dumps(
            {
                "status": "warning",
                "score": 97.5,
                "issues": [
                    {
                        "severity": "WARNING",
                        "code": "layout.text_density",
                        "message": "Estimated visible load is 50 words.",
                        "scene_id": "scene-001",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    preview.write_text("<html></html>", encoding="utf-8")
    decisions.write_text("# Decision report", encoding="utf-8")
    video.write_bytes(b"video fixture")

    paths = {"storyboard": storyboard, "lint": lint, "preview": preview, "decisions": decisions}
    monkeypatch.setattr("laka_video.web.init_project", lambda **_: None)
    monkeypatch.setattr("laka_video.web.compile_project", lambda _: paths)
    monkeypatch.setattr("laka_video.web.render_mp4", lambda *_args, **_kwargs: video)

    manager = QueuedManager(tmp_path / "jobs")
    response = create_app(manager=manager).test_client().post(
        "/jobs",
        data={"files": (io.BytesIO(b"audio fixture"), "voice.wav")},
        headers={"Accept": "application/json"},
    )
    manager._run_job(response.json["id"])
    job = manager.snapshot(response.json["id"])

    assert job is not None
    assert job["status"] == "complete"
    assert job["output"]["lint_status"] == "warning"
    assert job["output"]["warning_count"] == 1
    assert job["warnings"] == [
        "scene-001: layout.text_density: Estimated visible load is 50 words."
    ]
    assert "non-blocking quality note" in job["message"]
