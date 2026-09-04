import base64
import io
from pathlib import Path

from laka_video.web import JobManager, create_app


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
